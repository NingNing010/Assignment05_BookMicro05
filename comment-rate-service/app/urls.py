from django.urls import path
from .views import ReviewListCreate, ReviewDetail, BookReviews

urlpatterns = [
    path('reviews/', ReviewListCreate.as_view()),
    path('reviews/<int:pk>/', ReviewDetail.as_view()),
    path('reviews/book/<int:book_id>/', BookReviews.as_view()),
]
