from django.urls import path
from .views import OrderListCreate, OrderDetail

urlpatterns = [
    path('orders/', OrderListCreate.as_view()),
    path('orders/<int:order_id>/', OrderDetail.as_view()),
]
