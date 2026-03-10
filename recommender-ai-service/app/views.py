from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Recommendation
from .serializers import RecommendationSerializer
import requests
import random

BOOK_SERVICE_URL = "http://book-service:8000"
COMMENT_RATE_SERVICE_URL = "http://comment-rate-service:8000"


class RecommendationForCustomer(APIView):
    """Get AI-based recommendations for a customer"""

    def get(self, request, customer_id):
        # Simple recommendation: fetch all books and reviews,
        # recommend top-rated books the customer hasn't reviewed
        try:
            books_r = requests.get(f"{BOOK_SERVICE_URL}/books/")
            books = books_r.json()
        except Exception:
            books = []

        try:
            reviews_r = requests.get(f"{COMMENT_RATE_SERVICE_URL}/reviews/")
            reviews = reviews_r.json()
        except Exception:
            reviews = []

        # Books already reviewed by customer
        reviewed_book_ids = {
            r['book_id'] for r in reviews if r.get('customer_id') == customer_id
        }

        # Calculate average rating per book
        book_ratings = {}
        for review in reviews:
            bid = review.get('book_id')
            if bid not in book_ratings:
                book_ratings[bid] = []
            book_ratings[bid].append(review.get('rating', 0))

        recommendations = []
        for book in books:
            if book['id'] not in reviewed_book_ids:
                avg_rating = 0
                if book['id'] in book_ratings:
                    ratings = book_ratings[book['id']]
                    avg_rating = sum(ratings) / len(ratings)
                score = avg_rating + random.uniform(0, 1)  # Add randomness
                recommendations.append({
                    "book_id": book['id'],
                    "title": book.get('title', ''),
                    "score": round(score, 2),
                })

        # Sort by score descending, return top 5
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return Response(recommendations[:5])


class RecommendationList(APIView):
    def get(self, request):
        recs = Recommendation.objects.all()
        serializer = RecommendationSerializer(recs, many=True)
        return Response(serializer.data)
