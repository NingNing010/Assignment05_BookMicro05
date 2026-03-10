from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Review
from .serializers import ReviewSerializer
import requests

BOOK_SERVICE_URL = "http://book-service:8000"


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
