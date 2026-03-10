from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Page views
    path('books/', views.book_list, name='book_list'),
    path('publishers/', views.publisher_list, name='publisher_list'),
    path('cart/<int:customer_id>/', views.view_cart, name='view_cart'),
    path('customers/', views.customer_list, name='customer_list'),
    path('orders/', views.order_list, name='order_list'),
    path('payments/', views.payment_list, name='payment_list'),
    path('shipments/', views.shipment_list, name='shipment_list'),
    path('reviews/', views.review_list, name='review_list'),
    path('categories/', views.category_list, name='category_list'),
    path('recommendations/<int:customer_id>/', views.recommendations, name='recommendations'),
    path('staff/', views.staff_list, name='staff_list'),
    path('managers/', views.manager_list, name='manager_list'),

    # AI Agent
    path('agent/', views.agent_chat_page, name='agent_chat'),
    path('api/agent/chat/', views.agent_chat_api, name='agent_chat_api'),
    path('api/agent/help/', views.agent_help_api, name='agent_help_api'),

    # Generic API Proxy for frontend CRUD
    path('api/proxy/<str:service>/', views.api_proxy, name='api_proxy'),
    path('api/proxy/<str:service>/<path:path>', views.api_proxy, name='api_proxy_detail'),
]
