"""
ProductService — Application service orchestrating product use-cases.
"""
from __future__ import annotations
from typing import Optional
from modules.catalog.domain.entities.product import Product
from modules.catalog.domain.repositories.product_repository import ProductRepository


class ProductService:
    """
    Thin orchestration layer.  Receives a repository (injected)
    and delegates persistence while keeping the domain entities
    responsible for their own validation.
    """

    def __init__(self, repository: ProductRepository):
        self._repo = repository

    # ── Queries ────────────────────────────────

    def get_product(self, product_id: int) -> Optional[Product]:
        return self._repo.get_by_id(product_id)

    def list_products(self, product_type: Optional[str] = None) -> list[Product]:
        return self._repo.list_all(product_type=product_type)

    def filter_by_category(self, category_id: int) -> list[Product]:
        return self._repo.filter_by_category(category_id)

    def search_products(self, keyword: str) -> list[Product]:
        return self._repo.search(keyword)

    # ── Commands ───────────────────────────────

    def create_product(self, product: Product) -> Product:
        errors = product.validate()
        if errors:
            raise ValueError('; '.join(errors))
        return self._repo.save(product)

    def update_product(self, product: Product) -> Product:
        errors = product.validate()
        if errors:
            raise ValueError('; '.join(errors))
        return self._repo.save(product)

    def delete_product(self, product_id: int) -> bool:
        return self._repo.delete(product_id)
