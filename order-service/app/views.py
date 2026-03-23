from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem, SagaEvent
from .serializers import OrderSerializer, OrderItemSerializer
import requests
import json
import os
from decimal import Decimal, InvalidOperation

try:
    import pika
except Exception:
    pika = None

PAY_SERVICE_URL = "http://pay-service:8000"
SHIP_SERVICE_URL = "http://ship-service:8000"
CART_SERVICE_URL = "http://cart-service:8000"
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


def _resolve_item_price(cart_item):
    # Prefer price from cart payload if available.
    if cart_item.get("price") is not None:
        return _to_decimal(cart_item.get("price"), "0")

    # Fallback: fetch current price from book-service.
    book_id = cart_item.get("book_id")
    if not book_id:
        return Decimal("0")
    try:
        r = requests.get(f"http://book-service:8000/books/{book_id}/", timeout=5)
        if r.status_code == 200:
            book = r.json()
            return _to_decimal(book.get("price"), "0")
    except Exception:
        pass
    return Decimal("0")


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
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create order with Saga orchestration and compensating actions."""
        customer_id = request.data.get('customer_id')
        if not customer_id:
            return Response({"error": "customer_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        payment_method = request.data.get('payment_method', 'credit_card')
        shipping_method = request.data.get('shipping_method', 'standard')
        simulate_payment_failure = bool(request.data.get('simulate_payment_failure', False))
        simulate_shipping_failure = bool(request.data.get('simulate_shipping_failure', False))

        # Get cart items from cart-service
        try:
            r = requests.get(f"{CART_SERVICE_URL}/carts/{customer_id}/", timeout=5)
            cart_items = r.json()
        except Exception:
            cart_items = []

        if not cart_items:
            return Response({"error": "Cart is empty or unavailable"}, status=status.HTTP_400_BAD_REQUEST)

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
