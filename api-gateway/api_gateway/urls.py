from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Customer-facing Store (homepage) ──
    path('', views.store_home, name='store_home'),
    path('store/', views.store_home, name='store_home_alt'),
    path('store/products/', views.store_products, name='store_products'),
    path('store/product/<int:product_id>/', views.store_product_detail, name='store_product_detail'),
    path('store/cart/', views.store_cart, name='store_cart'),
    path('store/orders/', views.store_orders, name='store_orders'),
    path('store/reviews/', views.store_reviews, name='store_reviews'),
    path('store/payment/confirm/', views.store_payment_confirm, name='store_payment_confirm'),
    path('store/ai-advisor/', views.store_ai_advisor, name='store_ai_advisor'),
    path('store/login/', views.store_login, name='store_login'),
    path('store/register/', views.store_register, name='store_register'),

    # ── Admin Panel ──
    path('admin-panel/', views.dashboard, name='dashboard'),
    path('admin-panel/products/', views.product_list, name='product_list'),
    path('admin-panel/books/', views.product_list, name='book_list'),
    path('admin-panel/clothes/', views.product_list, name='clothes_list'),
    path('admin-panel/accounts/', views.account_list, name='account_list'),
    path('admin-panel/publishers/', views.publisher_list, name='publisher_list'),
    path('admin-panel/cart/<int:customer_id>/', views.view_cart, name='view_cart'),
    path('admin-panel/customers/', views.customer_list, name='customer_list'),
    path('admin-panel/orders/', views.order_list, name='order_list'),
    path('admin-panel/payments/', views.payment_list, name='payment_list'),
    path('admin-panel/shipments/', views.shipment_list, name='shipment_list'),
    path('admin-panel/reviews/', views.review_list, name='review_list'),
    path('admin-panel/categories/', views.category_list, name='category_list'),
    path('admin-panel/recommendations/<int:customer_id>/', views.recommendations, name='recommendations'),
    path('admin-panel/staff/', views.staff_list, name='staff_list'),
    path('admin-panel/managers/', views.manager_list, name='manager_list'),

    path('api/agent/chat/', views.agent_chat_api, name='agent_chat_api'),
    path('api/agent/help/', views.agent_help_api, name='agent_help_api'),

    # ── AI Service APIs ──
    path('api/track/', views.track_interaction, name='track_interaction'),
    path('api/ai/recommend/<int:customer_id>/', views.ai_recommend, name='ai_recommend'),

    # Generic API Proxy for frontend CRUD
    path('api/proxy/<str:service>/', views.api_proxy, name='api_proxy'),
    path('api/proxy/<str:service>/<path:path>', views.api_proxy, name='api_proxy_detail'),

    # Central auth-service proxy
    path('api/auth/<path:path>', views.auth_proxy, name='auth_proxy'),

    # Gateway health
    path('health/live/', views.health_live, name='gateway_health_live'),
    path('health/ready/', views.health_ready, name='gateway_health_ready'),
]
