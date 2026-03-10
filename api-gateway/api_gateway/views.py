from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json

BOOK_SERVICE_URL = "http://book-service:8000"
CART_SERVICE_URL = "http://cart-service:8000"
CUSTOMER_SERVICE_URL = "http://customer-service:8000"
STAFF_SERVICE_URL = "http://staff-service:8000"
ORDER_SERVICE_URL = "http://order-service:8000"
PAY_SERVICE_URL = "http://pay-service:8000"
SHIP_SERVICE_URL = "http://ship-service:8000"
COMMENT_RATE_SERVICE_URL = "http://comment-rate-service:8000"
CATALOG_SERVICE_URL = "http://catalog-service:8000"
RECOMMENDER_SERVICE_URL = "http://recommender-ai-service:8000"
MANAGER_SERVICE_URL = "http://manager-service:8000"

# ──────────────────────────────────────────────
# Service URL mapping for API proxy
# ──────────────────────────────────────────────
SERVICE_MAP = {
    'books': BOOK_SERVICE_URL,
    'publishers': BOOK_SERVICE_URL,
    'categories': BOOK_SERVICE_URL,
    'customers': CUSTOMER_SERVICE_URL,
    'carts': CART_SERVICE_URL,
    'cart-items': CART_SERVICE_URL,
    'orders': ORDER_SERVICE_URL,
    'payments': PAY_SERVICE_URL,
    'shipments': SHIP_SERVICE_URL,
    'reviews': COMMENT_RATE_SERVICE_URL,
    'staff': STAFF_SERVICE_URL,
    'managers': MANAGER_SERVICE_URL,
    'recommendations': RECOMMENDER_SERVICE_URL,
}


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────

def dashboard(request):
    return render(request, "dashboard.html")


# ──────────────────────────────────────────────
# Page views (render templates, data loaded via JS)
# ──────────────────────────────────────────────

def book_list(request):
    return render(request, "books.html")


def publisher_list(request):
    return render(request, "publishers.html")


def view_cart(request, customer_id):
    return render(request, "cart.html", {"customer_id": customer_id})


def customer_list(request):
    return render(request, "customers.html")


def order_list(request):
    return render(request, "orders.html")


def payment_list(request):
    return render(request, "payments.html")


def shipment_list(request):
    return render(request, "shipments.html")


def review_list(request):
    return render(request, "reviews.html")


def category_list(request):
    return render(request, "categories.html")


def recommendations(request, customer_id):
    return render(request, "recommendations.html", {"customer_id": customer_id})


def staff_list(request):
    return render(request, "staff.html")


def manager_list(request):
    return render(request, "managers.html")


# ──────────────────────────────────────────────
# Customer-facing Store Views
# ──────────────────────────────────────────────

def store_home(request):
    return render(request, "store/store_home.html")

def store_books(request):
    return render(request, "store/store_books.html")

def store_book_detail(request, book_id):
    return render(request, "store/store_book_detail.html", {"book_id": book_id})

def store_cart(request):
    return render(request, "store/store_cart.html")

def store_orders(request):
    return render(request, "store/store_orders.html")

def store_login(request):
    return render(request, "store/store_login.html")

def store_register(request):
    return render(request, "store/store_register.html")


# ──────────────────────────────────────────────
# Generic API Proxy — /api/proxy/<service>/<path>
# Forwards requests to the correct microservice
# ──────────────────────────────────────────────

@csrf_exempt
def api_proxy(request, service, path=''):
    """Generic proxy: /api/proxy/books/1/ → book-service:8000/books/1/"""
    base_url = SERVICE_MAP.get(service)
    if not base_url:
        return JsonResponse({"error": f"Unknown service: {service}"}, status=404)

    target_url = f"{base_url}/{service}/{path}"
    if not target_url.endswith('/'):
        target_url += '/'

    try:
        method = request.method
        headers = {'Content-Type': 'application/json'}

        if method == 'GET':
            resp = requests.get(target_url, timeout=10)
        elif method == 'POST':
            resp = requests.post(target_url, data=request.body, headers=headers, timeout=10)
        elif method == 'PUT':
            resp = requests.put(target_url, data=request.body, headers=headers, timeout=10)
        elif method == 'PATCH':
            resp = requests.patch(target_url, data=request.body, headers=headers, timeout=10)
        elif method == 'DELETE':
            resp = requests.delete(target_url, timeout=10)
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)

        # Return the upstream response
        try:
            data = resp.json()
            return JsonResponse(data, status=resp.status_code, safe=False)
        except ValueError:
            return HttpResponse(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type', 'text/plain'))

    except requests.ConnectionError:
        return JsonResponse({"error": f"Cannot connect to {service} service"}, status=503)
    except requests.Timeout:
        return JsonResponse({"error": f"Timeout connecting to {service} service"}, status=504)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ──────────────────────────────────────────────
# AI Agent Gateway Views
# ──────────────────────────────────────────────

def agent_chat_page(request):
    """Render the AI Agent chat UI page."""
    return render(request, "agent_chat.html")


@csrf_exempt
def agent_chat_api(request):
    """Proxy POST to customer-service agent chat endpoint."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    try:
        body = json.loads(request.body)
        r = requests.post(
            f"{CUSTOMER_SERVICE_URL}/agent/chat/",
            json=body,
            timeout=30,
        )
        return JsonResponse(r.json(), status=r.status_code)
    except requests.ConnectionError:
        return JsonResponse({"error": "Cannot connect to customer-service."}, status=503)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def agent_help_api(request):
    """Proxy GET to customer-service agent help endpoint."""
    try:
        r = requests.get(f"{CUSTOMER_SERVICE_URL}/agent/help/", timeout=10)
        return JsonResponse(r.json())
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
