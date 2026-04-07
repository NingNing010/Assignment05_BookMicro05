from django.urls import path
from .views import RegisterView, LoginView, RefreshView, ValidateView, MeView, UserListView, HealthLiveView, HealthReadyView

urlpatterns = [
    path('auth/register/', RegisterView.as_view()),
    path('auth/login/', LoginView.as_view()),
    path('auth/refresh/', RefreshView.as_view()),
    path('auth/validate/', ValidateView.as_view()),
    path('auth/me/', MeView.as_view()),
    path('auth/users/', UserListView.as_view()),
    path('health/live/', HealthLiveView.as_view()),
    path('health/ready/', HealthReadyView.as_view()),
]
