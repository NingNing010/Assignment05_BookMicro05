from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
import requests

PAY_SERVICE_URL = "http://pay-service:8000"
SHIP_SERVICE_URL = "http://ship-service:8000"
CART_SERVICE_URL = "http://cart-service:8000"


class OrderListCreate(APIView):
    def get(self, request):
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Create order from cart. Triggers payment and shipping.
        Expected: {customer_id, payment_method, shipping_method}
        """
        customer_id = request.data.get('customer_id')
        payment_method = request.data.get('payment_method', 'credit_card')
        shipping_method = request.data.get('shipping_method', 'standard')

        # Get cart items from cart-service
        try:
            r = requests.get(f"{CART_SERVICE_URL}/carts/{customer_id}/")
            cart_items = r.json()
        except Exception:
            cart_items = []

        # Create order
        order = Order.objects.create(
            customer_id=customer_id,
            payment_method=payment_method,
            shipping_method=shipping_method,
            status='pending'
        )

        total = 0
        for item in cart_items:
            oi = OrderItem.objects.create(
                order=order,
                book_id=item.get('book_id', 0),
                quantity=item.get('quantity', 1),
                price=item.get('price', 0)
            )
            total += oi.price * oi.quantity

        order.total_amount = total
        order.save()

        # Trigger payment via pay-service
        try:
            requests.post(f"{PAY_SERVICE_URL}/payments/", json={
                "order_id": order.id,
                "amount": str(order.total_amount),
                "method": payment_method,
            })
        except Exception:
            pass

        # Trigger shipping via ship-service
        try:
            requests.post(f"{SHIP_SERVICE_URL}/shipments/", json={
                "order_id": order.id,
                "customer_id": customer_id,
                "method": shipping_method,
            })
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
        'pending':   ['confirmed', 'cancelled'],
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
        return Response({"message": f"Order #{order_id} cancelled.", "status": "cancelled"})
