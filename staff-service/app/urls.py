from django.urls import path
from .views import StaffListCreate, StaffDetail, StaffManageBooks

urlpatterns = [
    path('staff/', StaffListCreate.as_view()),
    path('staff/<int:pk>/', StaffDetail.as_view()),
    path('staff/books/', StaffManageBooks.as_view()),
]
