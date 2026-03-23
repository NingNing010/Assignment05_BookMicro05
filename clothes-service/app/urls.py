from django.urls import path
from .views import ClothesListCreate, ClothesDetail, HealthLiveView, HealthReadyView

urlpatterns = [
    path('clothes/', ClothesListCreate.as_view()),
    path('clothes/<int:pk>/', ClothesDetail.as_view()),
    path('health/live/', HealthLiveView.as_view()),
    path('health/ready/', HealthReadyView.as_view()),
]
