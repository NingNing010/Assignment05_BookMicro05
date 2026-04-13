"""
Custom QuerySet / Manager for ProductModel.
"""
from django.db import models


class ProductQuerySet(models.QuerySet):

    def books(self):
        return self.filter(product_type__name='Book')

    def clothes(self):
        return self.filter(product_type__name='Clothes')

    def in_stock(self):
        return self.filter(stock__gt=0)

    def by_category(self, category_id):
        return self.filter(category_id=category_id)

    def by_price_range(self, min_price=None, max_price=None):
        qs = self
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)
        return qs

    def search(self, keyword):
        return self.filter(
            models.Q(name__icontains=keyword) |
            models.Q(description__icontains=keyword)
        )


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db).select_related(
            'product_type', 'category', 'brand',
        )
