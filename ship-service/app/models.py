from django.db import models


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reserved', 'Reserved'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order_id = models.IntegerField()
    customer_id = models.IntegerField()
    method = models.CharField(max_length=50, default='standard')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shipment for Order #{self.order_id}"
