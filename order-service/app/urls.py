from django.urls import path
from .views import OrderListCreate, OrderDetail, SagaEventList, HealthLiveView, HealthReadyView

urlpatterns = [
    path('orders/', OrderListCreate.as_view()),
    path('orders/<int:order_id>/', OrderDetail.as_view()),
    path('saga/events/', SagaEventList.as_view()),
    path('health/live/', HealthLiveView.as_view()),
    path('health/ready/', HealthReadyView.as_view()),
]
