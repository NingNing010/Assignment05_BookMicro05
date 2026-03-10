from django.urls import path
from .views import RecommendationForCustomer, RecommendationList

urlpatterns = [
    path('recommendations/', RecommendationList.as_view()),
    path('recommendations/<int:customer_id>/', RecommendationForCustomer.as_view()),
]
