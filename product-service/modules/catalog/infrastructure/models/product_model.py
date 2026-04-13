"""
Product ORM model — the single, unified product table.
Type-specific attributes live in the JSON `attributes` field.
"""
from django.db import models


class ProductModel(models.Model):
    name = models.CharField(max_length=255)
    product_type = models.ForeignKey(
        'catalog.ProductTypeModel',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products',
    )
    category = models.ForeignKey(
        'catalog.CategoryModel',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products',
    )
    brand = models.ForeignKey(
        'catalog.BrandModel',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products',
    )
    image_url = models.URLField(blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    description = models.TextField(blank=True, default='')
    attributes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'catalog_product'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
