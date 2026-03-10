from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
import requests

BOOK_SERVICE_URL = "http://book-service:8000"


class CartCreate(APIView):
    def post(self, request):
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddCartItem(APIView):
    def post(self, request):
        book_id = request.data.get("book_id")
        try:
            r = requests.get(f"{BOOK_SERVICE_URL}/books/")
            books = r.json()
            if not any(b["id"] == book_id for b in books):
                return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            pass  # Allow adding even if book-service is down
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ViewCart(APIView):
    def get(self, request, customer_id):
        try:
            cart = Cart.objects.get(customer_id=customer_id)
        except Cart.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)
        items = CartItem.objects.filter(cart=cart)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)

    def delete(self, request, customer_id):
        """Clear all items in a customer's cart."""
        try:
            cart = Cart.objects.get(customer_id=customer_id)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)
        CartItem.objects.filter(cart=cart).delete()
        return Response({"message": f"Cart cleared for customer #{customer_id}."}, status=status.HTTP_204_NO_CONTENT)


class CartItemDetail(APIView):
    """Update quantity or remove a cart item."""

    def get_object(self, pk):
        try:
            return CartItem.objects.get(pk=pk)
        except CartItem.DoesNotExist:
            return None

    def patch(self, request, pk):
        """Update cart item quantity: {"quantity": 3}"""
        item = self.get_object(pk)
        if not item:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CartItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Remove a single item from cart."""
        item = self.get_object(pk)
        if not item:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response({"message": f"Cart item #{pk} removed."}, status=status.HTTP_204_NO_CONTENT)
