"""
ProductRepositoryImpl — Concrete repository using Django ORM.
Implements the abstract ProductRepository interface from the domain layer.
"""
from __future__ import annotations
from typing import Optional
from django.db.models import Q

from modules.catalog.domain.entities.product import Product
from modules.catalog.domain.repositories.product_repository import ProductRepository
from modules.catalog.infrastructure.models.product_model import ProductModel


class ProductRepositoryImpl(ProductRepository):
    """Django ORM adapter for the Product aggregate root."""

    # ── Mapping helpers ────────────────────────

    @staticmethod
    def _to_entity(model: ProductModel) -> Product:
        return Product(
            id=model.id,
            name=model.name,
            product_type_id=model.product_type_id,
            category_id=model.category_id,
            brand_id=model.brand_id,
            image_url=model.image_url,
            price=model.price,
            stock=model.stock,
            description=model.description,
            attributes=model.attributes or {},
            created_at=str(model.created_at) if model.created_at else None,
            updated_at=str(model.updated_at) if model.updated_at else None,
        )

    # ── Queries ────────────────────────────────

    def get_by_id(self, product_id: int) -> Optional[Product]:
        try:
            obj = ProductModel.objects.select_related(
                'product_type', 'category', 'brand',
            ).get(pk=product_id)
            return self._to_entity(obj)
        except ProductModel.DoesNotExist:
            return None

    def list_all(self, product_type: Optional[str] = None) -> list[Product]:
        qs = ProductModel.objects.select_related('product_type', 'category', 'brand')
        if product_type:
            qs = qs.filter(product_type__name__iexact=product_type)
        return [self._to_entity(obj) for obj in qs]

    def filter_by_category(self, category_id: int) -> list[Product]:
        qs = ProductModel.objects.select_related(
            'product_type', 'category', 'brand',
        ).filter(category_id=category_id)
        return [self._to_entity(obj) for obj in qs]

    def search(self, keyword: str) -> list[Product]:
        qs = ProductModel.objects.select_related(
            'product_type', 'category', 'brand',
        ).filter(
            Q(name__icontains=keyword) |
            Q(description__icontains=keyword)
        )
        return [self._to_entity(obj) for obj in qs]

    # ── Commands ───────────────────────────────

    def save(self, product: Product) -> Product:
        if product.id:
            obj = ProductModel.objects.get(pk=product.id)
            obj.name = product.name
            obj.product_type_id = product.product_type_id
            obj.category_id = product.category_id
            obj.brand_id = product.brand_id
            obj.image_url = product.image_url
            obj.price = product.price
            obj.stock = product.stock
            obj.description = product.description
            obj.attributes = product.attributes
            obj.save()
        else:
            obj = ProductModel.objects.create(
                name=product.name,
                product_type_id=product.product_type_id,
                category_id=product.category_id,
                brand_id=product.brand_id,
                image_url=product.image_url,
                price=product.price,
                stock=product.stock,
                description=product.description,
                attributes=product.attributes,
            )
        return self._to_entity(obj)

    def delete(self, product_id: int) -> bool:
        deleted, _ = ProductModel.objects.filter(pk=product_id).delete()
        return deleted > 0
