"""
Brand ORM model — unifies the old Publisher (books) and Brand (clothes) concepts.
"""
from django.db import models


class BrandModel(models.Model):
    """
    Brand / Publisher.
    For books the brand is the publisher; for clothes it is the fashion brand.
    Optional address & email carry over from the old Publisher model.
    """
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, default='')
    email = models.EmailField(blank=True, default='')
    description = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'catalog_brand'
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'

    def __str__(self):
        return self.name
