from django.urls import path
from .views import CategoryListCreate, CategoryDetail, CatalogBooks

urlpatterns = [
    path('categories/', CategoryListCreate.as_view()),
    path('categories/<int:pk>/', CategoryDetail.as_view()),
    path('catalog/books/', CatalogBooks.as_view()),
]
