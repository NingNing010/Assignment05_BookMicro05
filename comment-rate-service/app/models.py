from django.db import models


class Review(models.Model):
    book_id = models.IntegerField()
    customer_id = models.IntegerField()
    rating = models.IntegerField()  # 1-5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for Book #{self.book_id} by Customer #{self.customer_id}"
