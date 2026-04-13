"""
ProductType ORM model.
"""
from django.db import models


class ProductTypeModel(models.Model):
    """Lookup table: Book, Clothes, Electronics, …"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'catalog_product_type'
        verbose_name = 'Product Type'
        verbose_name_plural = 'Product Types'

    def __str__(self):
        return self.name
