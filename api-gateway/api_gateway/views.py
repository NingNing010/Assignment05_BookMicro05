from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import os
import time
import uuid
import logging
import jwt

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
AUTH_SERVICE_URL = "http://auth-service:8000"
CLOTHES_SERVICE_URL = "http://clothes-service:8000"

JWT_SECRET = os.getenv("JWT_SECRET", "bookstore-jwt-secret")
JWT_ALGORITHM = "HS256"

RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_DEFAULT = int(os.getenv("RATE_LIMIT_DEFAULT", "120"))
RATE_LIMIT_GUEST = int(os.getenv("RATE_LIMIT_GUEST", "60"))
RATE_LIMIT_ADMIN = int(os.getenv("RATE_LIMIT_ADMIN", "300"))

logger = logging.getLogger("api_gateway")

# In-memory bucket for demo-level rate limiting.
_RATE_LIMIT_BUCKET = {}

# Service-level RBAC at gateway (Assignment 06 requirement).
SERVICE_ROLE_POLICY = {
    "orders": {"GET": ["customer", "staff", "manager", "admin"], "POST": ["customer", "staff", "manager", "admin"], "PATCH": ["customer", "staff", "manager", "admin"], "DELETE": ["customer", "staff", "manager", "admin"]},
    "payments": {"GET": ["staff", "manager", "admin"], "POST": ["staff", "manager", "admin"], "PUT": ["staff", "manager", "admin"], "PATCH": ["staff", "manager", "admin"], "DELETE": ["manager", "admin"]},
    "shipments": {"GET": ["staff", "manager", "admin"], "POST": ["staff", "manager", "admin"], "PUT": ["staff", "manager", "admin"], "PATCH": ["staff", "manager", "admin"], "DELETE": ["manager", "admin"]},
    "staff": {"GET": ["manager", "admin"], "POST": ["manager", "admin"], "PUT": ["manager", "admin"], "PATCH": ["manager", "admin"], "DELETE": ["admin"]},
    "managers": {"GET": ["admin"], "POST": ["admin"], "PUT": ["admin"], "PATCH": ["admin"], "DELETE": ["admin"]},
}

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
    'clothes': CLOTHES_SERVICE_URL,
}


def _extract_bearer_token(request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def _decode_access_token(token):
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")
    return payload


def _required_roles_for(service, method):
    return SERVICE_ROLE_POLICY.get(service, {}).get(method)


def _is_admin_panel_request(request):
    referer = request.headers.get('Referer', '')
    return '/admin-panel/' in referer


def _client_identity(request):
    token = _extract_bearer_token(request)
    if token:
        try:
            payload = _decode_access_token(token)
            return f"user:{payload.get('sub', 'unknown')}", payload
        except Exception:
            # Keep IP fallback for throttling even when token is invalid.
            pass
    ip = request.META.get("REMOTE_ADDR", "unknown")
    return f"ip:{ip}", None


def _allowed_requests_per_window(payload):
    if not payload:
        return RATE_LIMIT_GUEST
    role = payload.get("role", "customer")
    if role in ("admin", "manager", "staff"):
        return RATE_LIMIT_ADMIN
    return RATE_LIMIT_DEFAULT


def _is_rate_limited(request, bucket_name):
    now = time.time()
    identity, payload = _client_identity(request)
    key = f"{bucket_name}:{identity}"
    row = _RATE_LIMIT_BUCKET.get(key)
    limit = _allowed_requests_per_window(payload)

    if not row or now - row["start"] > RATE_LIMIT_WINDOW_SECONDS:
        _RATE_LIMIT_BUCKET[key] = {"count": 1, "start": now}
        return False

    row["count"] += 1
    return row["count"] > limit


def _with_request_id(response, request_id):
    response["X-Request-ID"] = request_id
    return response


def _log_request(request_id, request, target_url, status_code, started_at):
    elapsed_ms = int((time.time() - started_at) * 1000)
    logger.info(
        "proxy_request request_id=%s method=%s path=%s target=%s status=%s latency_ms=%s",
        request_id,
        request.method,
        request.path,
        target_url,
        status_code,
        elapsed_ms,
    )


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
    started_at = time.time()
    request_id = uuid.uuid4().hex[:12]

    if _is_rate_limited(request, "proxy"):
        return _with_request_id(JsonResponse({"error": "Rate limit exceeded"}, status=429), request_id)

    base_url = SERVICE_MAP.get(service)
    if not base_url:
        return _with_request_id(JsonResponse({"error": f"Unknown service: {service}"}, status=404), request_id)

    required_roles = _required_roles_for(service, request.method)
    jwt_payload = None
    if required_roles:
        token = _extract_bearer_token(request)
        if not token:
            # Compatibility for custom admin panel pages that do not yet use JWT in frontend.
            if _is_admin_panel_request(request):
                jwt_payload = {"role": "admin", "sub": "admin-panel"}
            else:
                return _with_request_id(JsonResponse({"error": "Missing bearer token"}, status=401), request_id)
        else:
            try:
                jwt_payload = _decode_access_token(token)
            except Exception:
                return _with_request_id(JsonResponse({"error": "Invalid or expired token"}, status=401), request_id)
        if jwt_payload.get("role") not in required_roles:
            return _with_request_id(JsonResponse({"error": "Insufficient role permissions"}, status=403), request_id)

    target_url = f"{base_url}/{service}/{path}"
    if not target_url.endswith('/'):
        target_url += '/'

    try:
        method = request.method
        headers = {'Content-Type': 'application/json', 'X-Request-ID': request_id}
        auth_header = request.headers.get('Authorization')
        if auth_header:
            headers['Authorization'] = auth_header

        if method == 'GET':
            resp = requests.get(target_url, params=request.GET, headers=headers, timeout=10)
        elif method == 'POST':
            resp = requests.post(target_url, data=request.body, headers=headers, timeout=10)
        elif method == 'PUT':
            resp = requests.put(target_url, data=request.body, headers=headers, timeout=10)
        elif method == 'PATCH':
            resp = requests.patch(target_url, data=request.body, headers=headers, timeout=10)
        elif method == 'DELETE':
            resp = requests.delete(target_url, params=request.GET, headers=headers, timeout=10)
        else:
            return _with_request_id(JsonResponse({"error": "Method not allowed"}, status=405), request_id)

        _log_request(request_id, request, target_url, resp.status_code, started_at)

        # Return the upstream response
        try:
            data = resp.json()
            return _with_request_id(JsonResponse(data, status=resp.status_code, safe=False), request_id)
        except ValueError:
            return _with_request_id(HttpResponse(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type', 'text/plain')), request_id)

    except requests.ConnectionError:
        return _with_request_id(JsonResponse({"error": f"Cannot connect to {service} service"}, status=503), request_id)
    except requests.Timeout:
        return _with_request_id(JsonResponse({"error": f"Timeout connecting to {service} service"}, status=504), request_id)
    except Exception as e:
        return _with_request_id(JsonResponse({"error": str(e)}, status=500), request_id)


@csrf_exempt
def auth_proxy(request, path=''):
    """Proxy auth routes to central auth-service: /api/auth/<path>."""
    request_id = uuid.uuid4().hex[:12]
    if _is_rate_limited(request, "auth"):
        return _with_request_id(JsonResponse({"error": "Rate limit exceeded"}, status=429), request_id)

    target_url = f"{AUTH_SERVICE_URL}/auth/{path}"
    if not target_url.endswith('/'):
        target_url += '/'

    try:
        method = request.method
        headers = {'Content-Type': 'application/json', 'X-Request-ID': request_id}
        auth_header = request.headers.get('Authorization')
        if auth_header:
            headers['Authorization'] = auth_header

        if method == 'GET':
            resp = requests.get(target_url, params=request.GET, headers=headers, timeout=10)
        elif method == 'POST':
            resp = requests.post(target_url, data=request.body, headers=headers, timeout=10)
        else:
            return _with_request_id(JsonResponse({"error": "Method not allowed"}, status=405), request_id)

        try:
            return _with_request_id(JsonResponse(resp.json(), status=resp.status_code, safe=False), request_id)
        except ValueError:
            return _with_request_id(HttpResponse(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type', 'text/plain')), request_id)
    except requests.ConnectionError:
        return _with_request_id(JsonResponse({"error": "Cannot connect to auth-service"}, status=503), request_id)
    except requests.Timeout:
        return _with_request_id(JsonResponse({"error": "Timeout connecting to auth-service"}, status=504), request_id)
    except Exception as e:
        return _with_request_id(JsonResponse({"error": str(e)}, status=500), request_id)


def health_live(request):
    return JsonResponse({"status": "live", "service": "api-gateway"})


def health_ready(request):
    checks = {}
    services = {
        "auth": AUTH_SERVICE_URL,
        "customer": CUSTOMER_SERVICE_URL,
        "book": BOOK_SERVICE_URL,
        "cart": CART_SERVICE_URL,
        "order": ORDER_SERVICE_URL,
        "clothes": CLOTHES_SERVICE_URL,
    }
    ready = True
    for name, url in services.items():
        try:
            # Treat reachable services as healthy even if they do not expose /health/live yet.
            r = requests.get(f"{url}/health/live/", timeout=2)
            checks[name] = r.status_code < 500
        except Exception:
            try:
                r = requests.get(url, timeout=2)
                checks[name] = r.status_code < 500
            except Exception:
                checks[name] = False
        ready = ready and checks[name]

    status_code = 200 if ready else 503
    return JsonResponse({"status": "ready" if ready else "degraded", "checks": checks}, status=status_code)


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
