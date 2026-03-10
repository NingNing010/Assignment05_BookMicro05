from django.urls import path
from .views import (
    BookListCreate, BookDetail,
    CategoryListCreate, CategoryDetail,
    PublisherListCreate, PublisherDetail,
)

urlpatterns = [
    path('books/', BookListCreate.as_view()),
    path('books/<int:pk>/', BookDetail.as_view()),
    path('categories/', CategoryListCreate.as_view()),
    path('categories/<int:pk>/', CategoryDetail.as_view()),
    path('publishers/', PublisherListCreate.as_view()),
    path('publishers/<int:pk>/', PublisherDetail.as_view()),
]
