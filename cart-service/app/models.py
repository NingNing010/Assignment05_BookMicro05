from django.db import models


class Cart(models.Model):
    customer_id = models.IntegerField()

    def __str__(self):
        return f"Cart for customer {self.customer_id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product_id = models.IntegerField()  # References product-service Product.id
    quantity = models.IntegerField()

    def __str__(self):
        return f"Product {self.product_id} x{self.quantity}"
