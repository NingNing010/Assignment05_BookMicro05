from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Recommendation
from .serializers import RecommendationSerializer
import requests
import random

PRODUCT_SERVICE_URL = "http://product-service:8000"
COMMENT_RATE_SERVICE_URL = "http://comment-rate-service:8000"


class RecommendationForCustomer(APIView):
    """Get AI-based recommendations for a customer using unified product-service"""

    def get(self, request, customer_id):
        # Fetch all products from unified product-service
        try:
            products_r = requests.get(f"{PRODUCT_SERVICE_URL}/products/")
            products = products_r.json()
        except Exception:
            products = []

        try:
            reviews_r = requests.get(f"{COMMENT_RATE_SERVICE_URL}/reviews/")
            reviews = reviews_r.json()
        except Exception:
            reviews = []

        # Products already reviewed by customer
        reviewed_product_ids = {
            r.get('book_id') or r.get('product_id')
            for r in reviews if r.get('customer_id') == customer_id
        }

        # Calculate average rating per product
        product_ratings = {}
        for review in reviews:
            pid = review.get('book_id') or review.get('product_id')
            if pid not in product_ratings:
                product_ratings[pid] = []
            product_ratings[pid].append(review.get('rating', 0))

        recommendations = []
        for product in products:
            pid = product['id']
            if pid not in reviewed_product_ids and product.get('stock', 0) > 0:
                avg_rating = 0
                if pid in product_ratings:
                    ratings = product_ratings[pid]
                    avg_rating = sum(ratings) / len(ratings)
                score = avg_rating + random.uniform(0, 1)
                recommendations.append({
                    "product_id": pid,
                    "name": product.get('name', ''),
                    "category": product.get('category_name', ''),
                    "price": float(product.get('price', 0)),
                    "score": round(score, 2),
                })

        # Sort by score descending, return top 10
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return Response(recommendations[:10])


class RecommendationList(APIView):
    def get(self, request):
        recs = Recommendation.objects.all()
        serializer = RecommendationSerializer(recs, many=True)
        return Response(serializer.data)
