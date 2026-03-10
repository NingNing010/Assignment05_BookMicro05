from django.db import models


class Staff(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=100, default='staff')

    def __str__(self):
        return self.name
