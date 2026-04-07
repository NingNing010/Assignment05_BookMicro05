from django.db import models


class Publisher(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, default='')
    email = models.EmailField(blank=True, default='')

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    image_url = models.URLField(blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    description = models.TextField(blank=True, default='')
    isbn = models.CharField(max_length=20, blank=True, default='')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='books'
    )
    publisher = models.ForeignKey(
        Publisher, on_delete=models.SET_NULL, null=True, blank=True, related_name='books'
    )

    def __str__(self):
        return self.title
