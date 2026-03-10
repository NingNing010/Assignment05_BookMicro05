from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, AgentConversation, AgentMessage
from .serializers import (
    CustomerSerializer,
    AgentChatInputSerializer,
    AgentConversationSerializer,
    AgentMessageSerializer,
)
from .agent import BookStoreAgent, HELP_TEXT
import requests

CART_SERVICE_URL = "http://cart-service:8000"


class CustomerListCreate(APIView):
    def get(self, request):
        customers = Customer.objects.all()
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            # Call cart-service to create cart for customer
            requests.post(
                f"{CART_SERVICE_URL}/carts/",
                json={"customer_id": customer.id}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerDetail(APIView):
    """GET / PUT / PATCH / DELETE a single customer."""

    def get_object(self, pk):
        try:
            return Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            return None

    def get(self, request, pk):
        customer = self.get_object(pk)
        if not customer:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(CustomerSerializer(customer).data)

    def put(self, request, pk):
        customer = self.get_object(pk)
        if not customer:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CustomerSerializer(customer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        customer = self.get_object(pk)
        if not customer:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CustomerSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        customer = self.get_object(pk)
        if not customer:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        customer.delete()
        return Response({"message": f"Customer #{pk} deleted."}, status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# AI Agent Endpoints
# ──────────────────────────────────────────────

class AgentChatView(APIView):
    """
    POST /agent/chat/
    Body: { "customer_id": 1, "message": "search books about Python", "conversation_id": null }

    The AI agent parses the message, executes the appropriate action
    across microservices, and returns the result.
    """

    def post(self, request):
        serializer = AgentChatInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        customer_id = serializer.validated_data['customer_id']
        message = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id')

        # Validate customer exists
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {"error": f"Customer #{customer_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get or create conversation
        if conversation_id:
            try:
                conversation = AgentConversation.objects.get(
                    id=conversation_id, customer=customer
                )
            except AgentConversation.DoesNotExist:
                conversation = AgentConversation.objects.create(customer=customer)
        else:
            conversation = AgentConversation.objects.create(customer=customer)

        # Save user message
        AgentMessage.objects.create(
            conversation=conversation,
            role='user',
            content=message,
        )

        # Process with AI agent
        agent = BookStoreAgent(customer_id=customer_id)
        result = agent.process(message)

        # Save agent response
        AgentMessage.objects.create(
            conversation=conversation,
            role='agent',
            content=result.get('message', ''),
            intent=result.get('intent', ''),
        )

        return Response({
            "conversation_id": conversation.id,
            "intent": result.get("intent", "unknown"),
            "message": result.get("message", ""),
            "data": {k: v for k, v in result.items() if k not in ("success", "message", "intent")},
            "success": result.get("success", False),
        })


class AgentConversationListView(APIView):
    """
    GET /agent/conversations/?customer_id=1
    List all conversations for a customer.
    """

    def get(self, request):
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response(
                {"error": "customer_id query param is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        conversations = AgentConversation.objects.filter(
            customer_id=customer_id
        ).order_by('-created_at')
        serializer = AgentConversationSerializer(conversations, many=True)
        return Response(serializer.data)


class AgentConversationDetailView(APIView):
    """
    GET /agent/conversations/<id>/
    Get full conversation with all messages.
    """

    def get(self, request, pk):
        try:
            conversation = AgentConversation.objects.get(pk=pk)
        except AgentConversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AgentConversationSerializer(conversation)
        return Response(serializer.data)


class AgentHelpView(APIView):
    """
    GET /agent/help/
    Returns available agent commands/capabilities.
    """

    def get(self, request):
        return Response({
            "help": HELP_TEXT,
            "commands": [
                {"action": "search_books", "examples": ["search books about Python", "tìm sách Django"]},
                {"action": "view_book", "examples": ["book #1", "chi tiết sách #1"]},
                {"action": "update_book_price", "examples": ["update book #1 price to 29.99", "cập nhật sách #1 giá 29.99"]},
                {"action": "add_to_cart", "examples": ["add book #3 to cart", "thêm sách #5 vào giỏ"]},
                {"action": "view_cart", "examples": ["view my cart", "xem giỏ hàng"]},
                {"action": "remove_cart_item", "examples": ["remove item #1 from cart", "xóa item #1 khỏi giỏ"]},
                {"action": "clear_cart", "examples": ["clear cart", "xóa hết giỏ hàng"]},
                {"action": "place_order", "examples": ["place order", "đặt hàng"]},
                {"action": "cancel_order", "examples": ["cancel order #1", "hủy đơn #1"]},
                {"action": "view_orders", "examples": ["view my orders", "xem đơn hàng"]},
                {"action": "rate_book", "examples": ["rate book #2 5 stars Great!", "đánh giá sách #2 5 sao"]},
                {"action": "get_reviews", "examples": ["reviews for book #1", "đánh giá sách #1"]},
                {"action": "get_recommendations", "examples": ["recommend", "gợi ý sách"]},
            ]
        })
