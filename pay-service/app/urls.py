from django.urls import path
from .views import PaymentListCreate, PaymentDetail

urlpatterns = [
    path('payments/', PaymentListCreate.as_view()),
    path('payments/<int:payment_id>/', PaymentDetail.as_view()),
]
