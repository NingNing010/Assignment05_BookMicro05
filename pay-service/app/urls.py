from django.urls import path
from .views import PaymentListCreate, PaymentDetail, PaymentReserve, PaymentRelease, HealthLiveView, HealthReadyView

urlpatterns = [
    path('payments/', PaymentListCreate.as_view()),
    path('payments/<int:payment_id>/', PaymentDetail.as_view()),
    path('payments/reserve/', PaymentReserve.as_view()),
    path('payments/release/', PaymentRelease.as_view()),
    path('health/live/', HealthLiveView.as_view()),
    path('health/ready/', HealthReadyView.as_view()),
]
