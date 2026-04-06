from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Review
from .serializers import ReviewSerializer
import requests
from .model_behavior import BehaviorModelService
from .knowledge_base import KnowledgeBaseManager
from .rag_advisor import BehaviorRAGAdvisor

BOOK_SERVICE_URL = "http://book-service:8000"
behavior_service = BehaviorModelService()
kb_manager = KnowledgeBaseManager()
rag_advisor = BehaviorRAGAdvisor()


class ReviewListCreate(APIView):
    def get(self, request):
        reviews = Review.objects.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Customer rates/comments on a book"""
        book_id = request.data.get('book_id')
        # Verify book exists via book-service
        try:
            r = requests.get(f"{BOOK_SERVICE_URL}/books/")
            books = r.json()
            if not any(b["id"] == book_id for b in books):
                return Response({"error": "Book not found"}, status=404)
        except Exception:
            pass

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors)


class ReviewDetail(APIView):
    """GET / PUT / PATCH / DELETE a single review."""

    def get_object(self, pk):
        try:
            return Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return None

    def get(self, request, pk):
        review = self.get_object(pk)
        if not review:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(ReviewSerializer(review).data)

    def put(self, request, pk):
        review = self.get_object(pk)
        if not review:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReviewSerializer(review, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Partial update — e.g. update rating: {"rating": 4}"""
        review = self.get_object(pk)
        if not review:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        review = self.get_object(pk)
        if not review:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
        review.delete()
        return Response({"message": f"Review #{pk} deleted."}, status=status.HTTP_204_NO_CONTENT)


class BookReviews(APIView):
    """Get all reviews for a specific book"""

    def get(self, request, book_id):
        reviews = Review.objects.filter(book_id=book_id)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class BehaviorModelTrain(APIView):
    """Train deep learning model_behavior from review data."""

    def post(self, request):
        epochs = int(request.data.get("epochs", 120))
        learning_rate = float(request.data.get("learning_rate", 0.01))
        reviews = Review.objects.all()
        try:
            result = behavior_service.train(reviews, epochs=epochs, lr=learning_rate)
            code = status.HTTP_200_OK if result.get("trained") else status.HTTP_400_BAD_REQUEST
            return Response(result, status=code)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BehaviorCustomerAnalyze(APIView):
    """Predict customer behavior segment and service advice."""

    def get(self, request, customer_id):
        reviews = Review.objects.all()
        try:
            result = behavior_service.predict_customer(customer_id=customer_id, reviews=reviews)
            code = status.HTTP_200_OK if result.get("found") else status.HTTP_404_NOT_FOUND
            return Response(result, status=code)
        except FileNotFoundError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KnowledgeBaseList(APIView):
    """List current KB documents used by RAG advisor."""

    def get(self, request):
        docs = kb_manager.load_documents()
        return Response({"count": len(docs), "documents": docs}, status=status.HTTP_200_OK)


class KnowledgeBaseRebuild(APIView):
    """Rebuild KB with optional custom docs from request body."""

    def post(self, request):
        extra_docs = request.data.get("documents", [])
        if extra_docs is None:
            extra_docs = []
        if not isinstance(extra_docs, list):
            return Response(
                {"error": "documents phai la list"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = kb_manager.rebuild(extra_docs=extra_docs)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RAGBehaviorChat(APIView):
    """RAG chat for customer behavior advisory."""

    def post(self, request):
        question = (request.data.get("question") or "").strip()
        customer_id = request.data.get("customer_id")
        if customer_id is not None:
            try:
                customer_id = int(customer_id)
            except Exception:
                return Response({"error": "customer_id khong hop le"}, status=status.HTTP_400_BAD_REQUEST)

        reviews = Review.objects.all()
        result = rag_advisor.ask(question=question, reviews=reviews, customer_id=customer_id)
        if result.get("error"):
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)
