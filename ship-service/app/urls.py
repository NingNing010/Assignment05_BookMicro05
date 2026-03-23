from django.urls import path
from .views import ShipmentListCreate, ShipmentDetail, ShipmentReserve, ShipmentRelease, HealthLiveView, HealthReadyView

urlpatterns = [
    path('shipments/', ShipmentListCreate.as_view()),
    path('shipments/<int:shipment_id>/', ShipmentDetail.as_view()),
    path('shipments/reserve/', ShipmentReserve.as_view()),
    path('shipments/release/', ShipmentRelease.as_view()),
    path('health/live/', HealthLiveView.as_view()),
    path('health/ready/', HealthReadyView.as_view()),
]
