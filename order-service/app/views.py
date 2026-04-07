from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem, SagaEvent
from .serializers import OrderSerializer, OrderItemSerializer
import requests
import json
import os
from decimal import Decimal, InvalidOperation
import math

try:
    import pika
except Exception:
    pika = None

PAY_SERVICE_URL = "http://pay-service:8000"
SHIP_SERVICE_URL = "http://ship-service:8000"
CART_SERVICE_URL = "http://cart-service:8000"
BOOK_SERVICE_URL = "http://book-service:8000"
CLOTHES_SERVICE_URL = "http://clothes-service:8000"
CLOTHES_PRODUCT_ID_OFFSET = 100000
EVENT_BUS_URL = os.getenv("EVENT_BUS_URL", "")
RABBITMQ_ENABLED = os.getenv("RABBITMQ_ENABLED", "false").lower() == "true"
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "bookstore.events")


def _to_decimal(value, default="0"):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _resolve_product_reference(product_id):
    try:
        numeric_id = int(product_id)
    except Exception:
        return None, None

    if numeric_id >= CLOTHES_PRODUCT_ID_OFFSET:
        return "clothes", numeric_id - CLOTHES_PRODUCT_ID_OFFSET
    return "book", numeric_id


def _get_product(product_id):
    product_type, real_id = _resolve_product_reference(product_id)
    if product_type == "clothes":
        try:
            r = requests.get(f"{CLOTHES_SERVICE_URL}/clothes/{real_id}/", timeout=5)
            if r.status_code == 200:
                return r.json(), product_type
        except Exception:
            pass
    try:
        r = requests.get(f"{BOOK_SERVICE_URL}/books/{real_id}/", timeout=5)
        if r.status_code == 200:
            return r.json(), "book"
    except Exception:
        pass
    return None, product_type or "book"


def _resolve_item_price(cart_item):
    # Prefer price from cart payload if available.
    if cart_item.get("price") is not None:
        return _to_decimal(cart_item.get("price"), "0")

    # Fallback: fetch current price from book-service.
    book_id = cart_item.get("book_id")
    if not book_id:
        return Decimal("0")
    try:
        product, _ = _get_product(book_id)
        if product:
            return _to_decimal(product.get("price"), "0")
    except Exception:
        pass
    return Decimal("0")


def _normalize_payment_method(method):
    raw = (method or "").strip().lower()
    mapping = {
        "cod": "cod",
        "cash_on_delivery": "cod",
        "chuyen_khoan": "bank_transfer",
        "chuyen khoan": "bank_transfer",
        "bank_transfer": "bank_transfer",
        "credit_card": "credit_card",
        "debit_card": "debit_card",
        "paypal": "paypal",
    }
    return mapping.get(raw, "credit_card")


def _get_book(book_id):
    try:
        r = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _publish_event(topic, payload):
    event_payload = json.dumps(payload, ensure_ascii=False)
    SagaEvent.objects.create(topic=topic, payload=event_payload)

    # Optional broker integration. If EVENT_BUS_URL is configured, publish a copy.
    if EVENT_BUS_URL:
        try:
            requests.post(EVENT_BUS_URL, json={"topic": topic, "payload": payload}, timeout=2)
        except Exception:
            pass

    # RabbitMQ topic exchange publish (Assignment 06 event bus integration).
    if RABBITMQ_ENABLED and pika:
        try:
            params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.exchange_declare(exchange=RABBITMQ_EXCHANGE, exchange_type='topic', durable=True)
            channel.basic_publish(
                exchange=RABBITMQ_EXCHANGE,
                routing_key=topic,
                body=event_payload.encode('utf-8'),
                properties=pika.BasicProperties(content_type='application/json', delivery_mode=2),
            )
            connection.close()
        except Exception:
            pass


class OrderListCreate(APIView):
    def get(self, request):
        orders = Order.objects.all().order_by('-created_at', '-id')

        customer_id = request.query_params.get('customer_id')
        if customer_id not in (None, ''):
            try:
                orders = orders.filter(customer_id=int(customer_id))
            except Exception:
                return Response({"error": "customer_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        page_raw = request.query_params.get('page')
        page_size_raw = request.query_params.get('page_size')
        use_pagination = page_raw is not None or page_size_raw is not None

        if not use_pagination:
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)

        try:
            page = max(1, int(page_raw or 1))
            page_size = max(1, min(100, int(page_size_raw or 10)))
        except Exception:
            return Response({"error": "page and page_size must be integers"}, status=status.HTTP_400_BAD_REQUEST)

        total = orders.count()
        total_pages = max(1, math.ceil(total / page_size))
        if page > total_pages:
            page = total_pages

        start = (page - 1) * page_size
        end = start + page_size
        serializer = OrderSerializer(orders[start:end], many=True)
        return Response({
            "results": serializer.data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        })

    def post(self, request):
        """Create order with Saga orchestration and compensating actions."""
        customer_id = request.data.get('customer_id')
        if not customer_id:
            return Response({"error": "customer_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        payment_method = _normalize_payment_method(request.data.get('payment_method', 'credit_card'))
        shipping_method = request.data.get('shipping_method', 'standard')
        receiver_name = (request.data.get('receiver_name') or '').strip()
        receiver_phone = (request.data.get('receiver_phone') or '').strip()
        shipping_address = (request.data.get('shipping_address') or '').strip()
        simulate_payment_failure = bool(request.data.get('simulate_payment_failure', False))
        simulate_shipping_failure = bool(request.data.get('simulate_shipping_failure', False))

        if not receiver_name or not receiver_phone or not shipping_address:
            return Response(
                {"error": "receiver_name, receiver_phone and shipping_address are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get cart items from cart-service
        try:
            r = requests.get(f"{CART_SERVICE_URL}/carts/{customer_id}/", timeout=5)
            cart_items = r.json()
        except Exception:
            cart_items = []

        if not cart_items:
            return Response({"error": "Cart is empty or unavailable"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate current stock before creating order.
        insufficient_items = []
        for item in cart_items:
            book_id = item.get('book_id')
            quantity = int(item.get('quantity', 1) or 1)
            book, product_type = _get_product(book_id)
            if not book:
                insufficient_items.append({
                    "book_id": book_id,
                    "requested": quantity,
                    "available": 0,
                    "title": f"{product_type.title()} #{book_id}",
                    "reason": "Book not found or unavailable",
                })
                continue

            available = int(book.get('stock') or 0)
            if quantity > available:
                insufficient_items.append({
                    "book_id": book_id,
                    "requested": quantity,
                    "available": available,
                    "title": book.get('title') or book.get('name') or f"{product_type.title()} #{book_id}",
                    "reason": "Insufficient stock",
                })

        if insufficient_items:
            detail_text = "; ".join(
                [f"{it['title']}: requested {it['requested']}, available {it['available']}" for it in insufficient_items]
            )
            return Response(
                {
                    "error": f"Some products do not have enough stock ({detail_text})",
                    "insufficient_items": insufficient_items,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Step 1: Create order (pending)
        order = Order.objects.create(
            customer_id=customer_id,
            payment_method=payment_method,
            shipping_method=shipping_method,
            status='pending'
        )
        _publish_event("order.created", {"order_id": order.id, "customer_id": customer_id, "status": order.status})

        total = Decimal("0")
        for item in cart_items:
            unit_price = _resolve_item_price(item)
            quantity = int(item.get('quantity', 1) or 1)
            oi = OrderItem.objects.create(
                order=order,
                book_id=item.get('book_id', 0),
                quantity=quantity,
                price=unit_price
            )
            total += oi.price * oi.quantity

        order.total_amount = total
        order.save()

        # Step 2: Reserve payment
        try:
            if simulate_payment_failure:
                raise RuntimeError("Simulated payment failure")

            pay_resp = requests.post(f"{PAY_SERVICE_URL}/payments/reserve/", json={
                "order_id": order.id,
                "amount": str(order.total_amount),
                "method": payment_method,
            }, timeout=8)
            if pay_resp.status_code >= 400:
                raise RuntimeError(f"Payment reserve failed: {pay_resp.text}")

            order.status = 'payment_reserved'
            order.save(update_fields=['status'])
            _publish_event("payment.reserved", {"order_id": order.id})
        except Exception as e:
            order.status = 'cancelled'
            order.save(update_fields=['status'])
            _publish_event("payment.failed", {"order_id": order.id, "reason": str(e)})
            _publish_event("order.cancelled", {"order_id": order.id, "phase": "payment"})
            serializer = OrderSerializer(order)
            return Response({"error": "Payment reservation failed", "order": serializer.data}, status=status.HTTP_502_BAD_GATEWAY)

        # Step 3: Reserve shipping
        try:
            if simulate_shipping_failure:
                raise RuntimeError("Simulated shipping failure")

            ship_resp = requests.post(f"{SHIP_SERVICE_URL}/shipments/reserve/", json={
                "order_id": order.id,
                "customer_id": customer_id,
                "method": shipping_method,
                "receiver_name": receiver_name,
                "receiver_phone": receiver_phone,
                "shipping_address": shipping_address,
            }, timeout=8)
            if ship_resp.status_code >= 400:
                raise RuntimeError(f"Shipping reserve failed: {ship_resp.text}")

            order.status = 'shipping_reserved'
            order.save(update_fields=['status'])
            _publish_event("shipping.reserved", {"order_id": order.id})
        except Exception as e:
            # Step 5: Compensate payment if shipping reserve fails.
            order.status = 'compensating'
            order.save(update_fields=['status'])
            _publish_event("shipping.failed", {"order_id": order.id, "reason": str(e)})

            try:
                requests.post(f"{PAY_SERVICE_URL}/payments/release/", json={"order_id": order.id}, timeout=8)
                _publish_event("payment.released", {"order_id": order.id})
            except Exception:
                pass

            order.status = 'cancelled'
            order.save(update_fields=['status'])
            _publish_event("order.cancelled", {"order_id": order.id, "phase": "shipping"})
            serializer = OrderSerializer(order)
            return Response({"error": "Shipping reservation failed", "order": serializer.data}, status=status.HTTP_502_BAD_GATEWAY)

        # Step 4: Confirm order
        order.status = 'confirmed'
        order.save(update_fields=['status'])
        _publish_event("order.confirmed", {"order_id": order.id})

        # Step 5: Reduce stock after successful confirmation.
        stock_update_errors = []
        for item in cart_items:
            book_id = item.get('book_id')
            quantity = int(item.get('quantity', 1) or 1)
            book, product_type = _get_product(book_id)
            if not book:
                stock_update_errors.append({"book_id": book_id, "reason": f"{product_type.title()} not found when updating stock"})
                continue

            current_stock = int(book.get('stock') or 0)
            new_stock = max(0, current_stock - quantity)
            try:
                _, real_id = _resolve_product_reference(book_id)
                if product_type == "clothes":
                    requests.patch(f"{CLOTHES_SERVICE_URL}/clothes/{real_id}/", json={"stock": new_stock}, timeout=8)
                else:
                    requests.patch(f"{BOOK_SERVICE_URL}/books/{real_id}/", json={"stock": new_stock}, timeout=8)
            except Exception as e:
                stock_update_errors.append({"book_id": book_id, "reason": str(e)})

        if stock_update_errors:
            _publish_event("stock.update.partial_failed", {"order_id": order.id, "errors": stock_update_errors})

        # Step 6: Clear cart after successful order placement.
        try:
            requests.delete(f"{CART_SERVICE_URL}/carts/{customer_id}/", timeout=8)
        except Exception:
            pass

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderDetail(APIView):
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    # Valid status transitions
    TRANSITIONS = {
        'pending':   ['payment_reserved', 'cancelled'],
        'payment_reserved': ['shipping_reserved', 'compensating', 'cancelled'],
        'shipping_reserved': ['confirmed', 'compensating', 'cancelled'],
        'compensating': ['cancelled'],
        'confirmed': ['shipped', 'cancelled'],
        'shipped':   ['delivered'],
        'delivered': [],
        'cancelled': [],
    }

    def patch(self, request, order_id):
        """Update order status: {"status": "confirmed"}"""
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        new_status = request.data.get('status')
        if new_status:
            allowed = self.TRANSITIONS.get(order.status, [])
            if new_status not in allowed:
                return Response(
                    {"error": f"Cannot change from '{order.status}' to '{new_status}'. Allowed: {allowed}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, order_id):
        """Cancel an order (set status to cancelled)."""
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        if order.status in ('shipped', 'delivered'):
            return Response({"error": "Cannot cancel a shipped/delivered order."}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'cancelled'
        order.save()
        _publish_event("order.cancelled", {"order_id": order.id, "phase": "manual"})
        return Response({"message": f"Order #{order_id} cancelled.", "status": "cancelled"})


class SagaEventList(APIView):
    def get(self, request):
        events = SagaEvent.objects.all().order_by('-id')[:200]
        data = [{"id": e.id, "topic": e.topic, "payload": e.payload, "created_at": e.created_at} for e in events]
        return Response(data)


class HealthLiveView(APIView):
    def get(self, request):
        return Response({"status": "live", "service": "order-service"})


class HealthReadyView(APIView):
    def get(self, request):
        Order.objects.count()
        return Response({"status": "ready", "service": "order-service"})
