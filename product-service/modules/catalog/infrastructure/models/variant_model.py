"""
Variant ORM model — product variants (size + color combinations).
"""
from django.db import models


class VariantModel(models.Model):
    product = models.ForeignKey(
        'catalog.ProductModel',
        on_delete=models.CASCADE,
        related_name='variants',
    )
    sku = models.CharField(max_length=100, blank=True, default='')
    size = models.CharField(max_length=50, blank=True, default='')
    color = models.CharField(max_length=50, blank=True, default='')
    price_override = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
    )
    stock = models.IntegerField(default=0)

    class Meta:
        db_table = 'catalog_variant'
        verbose_name = 'Variant'
        verbose_name_plural = 'Variants'

    def __str__(self):
        parts = [self.product.name]
        if self.size:
            parts.append(self.size)
        if self.color:
            parts.append(self.color)
        return ' / '.join(parts)
