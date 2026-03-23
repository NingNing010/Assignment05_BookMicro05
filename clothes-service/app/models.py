from django.db import models


class Clothes(models.Model):
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255, blank=True, default='')
    size = models.CharField(max_length=50, blank=True, default='')
    color = models.CharField(max_length=50, blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name
