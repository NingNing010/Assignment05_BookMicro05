from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
import requests

BOOK_SERVICE_URL = "http://book-service:8000"
CLOTHES_SERVICE_URL = "http://clothes-service:8000"
CLOTHES_PRODUCT_ID_OFFSET = 100000


def _resolve_product_reference(product_id):
    try:
        numeric_id = int(product_id)
    except Exception:
        return None, None

    if numeric_id >= CLOTHES_PRODUCT_ID_OFFSET:
        return "clothes", numeric_id - CLOTHES_PRODUCT_ID_OFFSET
    return "book", numeric_id


def _get_product_stock(product_id):
    product_type, real_id = _resolve_product_reference(product_id)
    if product_type == "clothes":
        try:
            r = requests.get(f"{CLOTHES_SERVICE_URL}/clothes/{real_id}/", timeout=5)
            if r.status_code == 200:
                product = r.json()
                return int(product.get("stock") or 0), (product.get("name") or f"Clothes #{real_id}"), product_type
        except Exception:
            pass
    try:
        r = requests.get(f"{BOOK_SERVICE_URL}/books/{real_id}/", timeout=5)
        if r.status_code == 200:
            book = r.json()
            return int(book.get("stock") or 0), (book.get("title") or f"Book #{real_id}"), product_type
    except Exception:
        pass
    return None, None, product_type or "book"


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
        customer_id = request.data.get("customer_id")
        quantity = request.data.get("quantity", 1)
        item_type = (request.data.get("item_type") or "book").strip().lower()

        if not customer_id:
            return Response({"error": "customer_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if item_type not in {"book", "clothes"}:
            item_type = "book"

        # Auto-create cart for customer if it doesn't exist
        cart, _ = Cart.objects.get_or_create(customer_id=customer_id)

        requested_qty = int(quantity or 1)
        stock, title, resolved_type = _get_product_stock(book_id)
        if stock is not None and stock < 1:
            return Response({"error": f"'{title}' is out of stock"}, status=status.HTTP_409_CONFLICT)

        if resolved_type:
            item_type = resolved_type

        # Check if book already in cart – if so, increment quantity
        existing = CartItem.objects.filter(cart=cart, book_id=book_id).first()
        if existing:
            new_qty = existing.quantity + requested_qty
            if stock is not None and new_qty > stock:
                return Response(
                    {
                        "error": f"Only {stock} item(s) available for '{title}'. Please reduce quantity.",
                        "available": stock,
                        "requested": new_qty,
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            existing.quantity = new_qty
            existing.save()
            return Response(CartItemSerializer(existing).data, status=status.HTTP_200_OK)

        # Validate book exists (optional, non-blocking)
        try:
            if item_type == "clothes":
                r = requests.get(f"{CLOTHES_SERVICE_URL}/clothes/{_resolve_product_reference(book_id)[1]}/", timeout=5)
                if r.status_code == 404:
                    return Response({"error": "Clothes not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                r = requests.get(f"{BOOK_SERVICE_URL}/books/{_resolve_product_reference(book_id)[1]}/", timeout=5)
                if r.status_code == 404:
                    return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            pass  # Allow adding even if product-service is down

        if stock is not None and requested_qty > stock:
            return Response(
                {
                    "error": f"Only {stock} item(s) available for '{title}'.",
                    "available": stock,
                    "requested": requested_qty,
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer = CartItemSerializer(data={"cart": cart.id, "book_id": book_id, "quantity": requested_qty})
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

        new_qty = int(request.data.get("quantity", item.quantity) or item.quantity)
        stock, title, _ = _get_product_stock(item.book_id)
        if stock is not None and new_qty > stock:
            return Response(
                {
                    "error": f"Only {stock} item(s) available for '{title}'.",
                    "available": stock,
                    "requested": new_qty,
                },
                status=status.HTTP_409_CONFLICT,
            )

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
