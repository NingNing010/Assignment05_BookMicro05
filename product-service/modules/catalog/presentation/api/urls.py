"""
URL configuration for the Catalog (Product) API.

Backward-compatible routes:
  /books/, /books/<pk>/
  /clothes/, /clothes/<pk>/
  /categories/, /categories/<pk>/
  /publishers/, /publishers/<pk>/
  /catalog/books/

New DDD routes:
  /products/, /products/<pk>/
  /brands/, /product-types/, /variants/
"""
from django.urls import path
from modules.catalog.presentation.api.views.product_view import (
    ProductListCreate, ProductDetail,
    BookListCreate, BookDetail,
    ClothesListCreate, ClothesDetail,
    PublisherListCreate, PublisherDetail,
    BrandListCreate,
    ProductTypeListCreate,
    VariantListCreate,
    HealthLiveView, HealthReadyView,
)
from modules.catalog.presentation.api.views.category_view import (
    CategoryListCreate, CategoryDetail, CatalogBooks,
)

urlpatterns = [
    # ── Unified Product endpoints ──────────────
    path('products/', ProductListCreate.as_view()),
    path('products/<int:pk>/', ProductDetail.as_view()),

    # ── Backward-compatible Book endpoints ─────
    path('books/', BookListCreate.as_view()),
    path('books/<int:pk>/', BookDetail.as_view()),

    # ── Backward-compatible Clothes endpoints ──
    path('clothes/', ClothesListCreate.as_view()),
    path('clothes/<int:pk>/', ClothesDetail.as_view()),

    # ── Category endpoints ─────────────────────
    path('categories/', CategoryListCreate.as_view()),
    path('categories/<int:pk>/', CategoryDetail.as_view()),

    # ── Backward-compatible Publisher → Brand ──
    path('publishers/', PublisherListCreate.as_view()),
    path('publishers/<int:pk>/', PublisherDetail.as_view()),

    # ── Catalog proxy (backward compat) ────────
    path('catalog/books/', CatalogBooks.as_view()),

    # ── New DDD endpoints ──────────────────────
    path('brands/', BrandListCreate.as_view()),
    path('product-types/', ProductTypeListCreate.as_view()),
    path('variants/', VariantListCreate.as_view()),

    # ── Health checks ──────────────────────────
    path('health/live/', HealthLiveView.as_view()),
    path('health/ready/', HealthReadyView.as_view()),
]
