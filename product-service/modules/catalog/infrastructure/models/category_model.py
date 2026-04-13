"""
Category ORM model — supports tree structure via parent FK.
"""
from django.db import models


class CategoryModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='children',
    )

    class Meta:
        db_table = 'catalog_category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name
