from django.db import models


class Recommendation(models.Model):
    customer_id = models.IntegerField()
    book_id = models.IntegerField()
    score = models.FloatField(default=0.0)  # AI recommendation score
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommend Book #{self.book_id} for Customer #{self.customer_id} (score: {self.score})"
