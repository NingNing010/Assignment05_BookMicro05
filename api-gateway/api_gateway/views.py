from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import os
import time
import uuid
import logging
import re
import jwt
import unicodedata

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


def _normalize_text(text):
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower()


def _extract_topic_from_question(question):
    """Extract topic/category name from question using quoted text or keywords."""
    import re
    
    # Try to extract quoted text: "AI", "Python", etc.
    quoted = re.findall(r'"([^"]+)"', question)
    if quoted:
        topic = quoted[0].strip()
        category = _lookup_book_category_by_title(topic)
        if category:
            return category
        # Map common topics to actual category names
        topic_map = {
            "ai": "Data Science",
            "machine learning": "Data Science",
            "ml": "Data Science",
            "python": "Programming",
            "javascript": "Programming",
            "js": "Programming",
            "java": "Programming",
            "database": "Architecture",
            "web": "Programming",
            "mobile": "Programming",
            "dev": "DevOps",
            "devops": "DevOps",
            "docker": "DevOps",
            "kubernetes": "DevOps",
            "nau an": "Cooking",
            "am thuc": "Cooking",
            "doi song": "Lifestyle",
            "song khoe": "Lifestyle",
            "vat dung": "Household",
            "gia dung": "Household",
            "kinh doanh": "Business",
            "finance": "Business",
            "tre em": "Children",
            "thieu nhi": "Children",
        }
        return topic_map.get(topic.lower(), topic)
    
    # Try common topic keywords in the question (case-insensitive, Vietnamese)
    topic_mapping = {
        "Data Science": ["ai", "artificial intelligence", "trí tuệ nhân tạo", "machine learning", "ml", "dữ liệu", "data"],
        "Programming": ["python", "javascript", "js", "java", "lập trình", "code", "coding"],
        "DevOps": ["dev", "devops", "docker", "kubernetes", "deployment", "ci/cd"],
        "Architecture": ["architecture", "thiết kế", "system design", "microservices"],
        "Cooking": ["nấu ăn", "am thuc", "ẩm thực", "recipe", "cook", "cooking", "bep", "món ăn"],
        "Lifestyle": ["đời sống", "song khoe", "lifestyle", "self help", "wellness", "sức khỏe", "thói quen"],
        "Household": ["vật dụng", "gia dung", "household", "home", "nhà cửa", "dọn dẹp", "tối giản"],
        "Business": ["kinh doanh", "business", "startup", "marketing", "sales", "finance", "tài chính"],
        "Children": ["trẻ em", "thiếu nhi", "children", "kids", "kid", "nuoi day con", "nuôi dạy con"],
    }
    
    normalized = _normalize_text(question)
    for category, keywords in topic_mapping.items():
        for kw in keywords:
            if kw in normalized:
                return category
    
    return None


def _extract_complaint_exclusion_terms(question):
    """Extract likely topic/title terms to exclude from complaint recommendations."""
    import re

    terms = []
    quoted = re.findall(r'"([^"]+)"', question)
    if quoted:
        terms.append(_normalize_text(quoted[0]))

    normalized = _normalize_text(question)
    tokens = re.findall(r"[a-z0-9]+", normalized)
    stopwords = {
        "toi", "cuon", "sach", "nay", "nay", "do", "ve", "va", "rat", "that",
        "vong", "nen", "xu", "ly", "the", "nao", "khong", "thich", "ghet",
        "thatvong", "khonghailong", "bo", "di", "roi", "boi", "luon", "tui",
        "cho", "minh", "dung", "co", "nen", "mot", "hai", "ba", "ban", "cua"
    }

    for token in tokens:
        if len(token) >= 3 and token not in stopwords:
            terms.append(token)

    unique_terms = []
    seen = set()
    for term in terms:
        if term and term not in seen:
            seen.add(term)
            unique_terms.append(term)
    return unique_terms


def _lookup_book_category_by_title(book_title):
    """Look up a book title in the catalog and return its category name."""
    try:
        all_books_res = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
        if all_books_res.status_code != 200:
            return None

        all_books = all_books_res.json()
        if not isinstance(all_books, list):
            return None

        normalized_title = _normalize_text(book_title)
        for book in all_books:
            if _normalize_text(book.get("title", "")) == normalized_title:
                return book.get("category_name")
    except Exception:
        return None

    return None


def _fetch_catalog_books():
    """Fetch the full book catalog once for scoring and filtering."""
    try:
        books_res = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
        if books_res.status_code != 200:
            return []

        books = books_res.json()
        return books if isinstance(books, list) else []
    except Exception:
        return []


def _collect_customer_preferences(customer_id, books):
    """Build lightweight preference signals from customer order/review history."""
    profile = {
        "liked_categories": set(),
        "disliked_categories": set(),
        "liked_tokens": set(),
    }
    if not customer_id:
        return profile

    book_by_id = {int(b.get("id")): b for b in books if b.get("id") is not None}

    try:
        orders_res = requests.get(f"{ORDER_SERVICE_URL}/orders/", timeout=5)
        if orders_res.status_code == 200:
            orders = orders_res.json()
            if isinstance(orders, list):
                for order in orders:
                    if int(order.get("customer_id") or 0) != int(customer_id):
                        continue
                    if (order.get("status") or "").lower() == "cancelled":
                        continue
                    items = order.get("items") or []
                    for item in items:
                        book = book_by_id.get(int(item.get("book_id") or 0))
                        if not book:
                            continue
                        category = book.get("category_name")
                        if category:
                            profile["liked_categories"].add(_normalize_text(category))
                        for token in re.findall(r"[a-z0-9]+", _normalize_text(book.get("title", ""))):
                            if len(token) >= 4:
                                profile["liked_tokens"].add(token)
    except Exception:
        pass

    try:
        reviews_res = requests.get(f"{COMMENT_RATE_SERVICE_URL}/reviews/", timeout=5)
        if reviews_res.status_code == 200:
            reviews = reviews_res.json()
            if isinstance(reviews, list):
                for review in reviews:
                    if int(review.get("customer_id") or 0) != int(customer_id):
                        continue
                    book = book_by_id.get(int(review.get("book_id") or 0))
                    if not book:
                        continue
                    category_norm = _normalize_text(book.get("category_name", ""))
                    rating = int(review.get("rating") or 0)
                    if rating >= 4 and category_norm:
                        profile["liked_categories"].add(category_norm)
                    if rating <= 2 and category_norm:
                        profile["disliked_categories"].add(category_norm)
    except Exception:
        pass

    return profile


def _related_categories_for(category_name):
    """Return near-related categories for upsell-style suggestions."""
    if not category_name:
        return []

    related_map = {
        "programming": ["Architecture", "DevOps"],
        "data science": ["Programming", "Architecture", "DevOps"],
        "architecture": ["Programming", "DevOps", "Data Science"],
        "devops": ["Architecture", "Programming"],
        "cooking": ["Lifestyle", "Household"],
        "lifestyle": ["Cooking", "Business", "Children"],
        "household": ["Lifestyle", "Cooking"],
        "business": ["Lifestyle", "Programming"],
        "children": ["Lifestyle", "Cooking"],
    }
    return related_map.get(_normalize_text(category_name), [])


def _book_match_score(question, book, focus_category=None, related_categories=None, focus_terms=None, exact_title=None, allow_related=True, customer_profile=None):
    """Score a book against the question for ranked recommendations."""
    title = _normalize_text(book.get("title", ""))
    category = _normalize_text(book.get("category_name", ""))
    description = _normalize_text(book.get("description", ""))
    question_tokens = set(re.findall(r"[a-z0-9]+", _normalize_text(question)))

    score = 0
    normalized_focus_category = _normalize_text(focus_category) if focus_category else ""
    normalized_exact_title = _normalize_text(exact_title) if exact_title else ""
    normalized_related = {_normalize_text(name) for name in (related_categories or []) if name}

    if normalized_exact_title and title == normalized_exact_title:
        score += 1000

    if normalized_focus_category and category == normalized_focus_category:
        score += 260
    elif allow_related and normalized_related and category in normalized_related:
        score += 140

    for term in (focus_terms or []):
        normalized_term = _normalize_text(term)
        if not normalized_term:
            continue
        if normalized_term in title:
            score += 140
        if normalized_term in category:
            score += 80
        if normalized_term in description:
            score += 20

    title_tokens = set(re.findall(r"[a-z0-9]+", title))
    score += len(title_tokens.intersection(question_tokens)) * 18

    if normalized_focus_category and category == normalized_focus_category:
        score += len(title_tokens.intersection(question_tokens)) * 8

    if "dev" in question_tokens and ("dev" in title or "dev" in category):
        score += 120

    customer_profile = customer_profile or {}
    liked_categories = customer_profile.get("liked_categories") or set()
    disliked_categories = customer_profile.get("disliked_categories") or set()
    liked_tokens = customer_profile.get("liked_tokens") or set()

    strict_topic_mode = bool(normalized_focus_category) and not allow_related

    if category in liked_categories and (not strict_topic_mode or category == normalized_focus_category):
        score += 90
    if category in disliked_categories:
        score -= 120

    for token in liked_tokens:
        if token in title:
            score += 24

    return score


def _recommend_books_for_question(question, focus_category=None, max_items=4, allow_related=True, customer_id=None):
    """Rank books for purchase / upsell flows."""
    books = _fetch_catalog_books()

    quoted = re.findall(r'"([^"]+)"', question)
    exact_title = quoted[0].strip() if quoted else None
    focus_terms = _extract_complaint_exclusion_terms(question)
    if exact_title:
        normalized_exact = _normalize_text(exact_title)
        if normalized_exact not in focus_terms:
            focus_terms.append(normalized_exact)

    related_categories = _related_categories_for(focus_category) if allow_related else []
    customer_profile = _collect_customer_preferences(customer_id, books)

    ranked = []
    for book in books:
        if int(book.get("stock", 0) or 0) <= 0:
            continue

        score = _book_match_score(
            question=question,
            book=book,
            focus_category=focus_category,
            related_categories=related_categories,
            focus_terms=focus_terms,
            exact_title=exact_title,
            allow_related=allow_related,
            customer_profile=customer_profile,
        )

        if score > 0:
            ranked.append((score, book))

    ranked.sort(key=lambda item: (-item[0], item[1].get("title", "")))
    selected = [book for _, book in ranked[:max_items]]

    # For upsell-style flows, make sure nearby categories appear even if the exact
    # category dominates the score. This gives a broader, more useful mix.
    if allow_related and focus_category:
        selected_ids = {book.get("id") for book in selected}
        for related_category in _related_categories_for(focus_category):
            related_books = _fetch_books_by_category(related_category)
            for book in related_books:
                if book.get("id") in selected_ids:
                    continue
                selected.append(book)
                selected_ids.add(book.get("id"))
                if len(selected) >= max_items:
                    break
            if len(selected) >= max_items:
                break

    if not selected:
        # Final fallback: always return a few in-stock books instead of an empty UI.
        in_stock = [book for book in books if int(book.get("stock", 0) or 0) > 0]
        return in_stock[:max_items]

    return selected[:max_items]


def _fetch_books_by_category(category_name):
    """Fetch books from book service filtered by category."""
    try:
        all_books_res = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
        if all_books_res.status_code != 200:
            return []
        
        all_books = all_books_res.json()
        if not isinstance(all_books, list):
            return []
        
        # Filter by category name (case-insensitive)
        category_lower = category_name.lower()
        filtered = [
            b for b in all_books 
            if b.get("category_name", "").lower() == category_lower and b.get("stock", 0) > 0
        ]
        
        # Return up to 4 books for UI display
        return filtered[:4]
    except Exception:
        return []


def _fetch_other_category_books(excluded_category, excluded_title=None, excluded_terms=None):
    """Fetch books from different categories (for complaint scenario)."""
    try:
        all_books_res = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
        if all_books_res.status_code != 200:
            return []
        
        all_books = all_books_res.json()
        if not isinstance(all_books, list):
            return []
        
        # Filter out the excluded category and get in-stock books
        excluded_lower = excluded_category.lower() if excluded_category else ""
        excluded_title_lower = _normalize_text(excluded_title) if excluded_title else ""
        excluded_terms = [term for term in (excluded_terms or []) if term]
        filtered = [
            b for b in all_books 
            if b.get("category_name", "").lower() != excluded_lower
            and _normalize_text(b.get("title", "")) != excluded_title_lower
            and not any(term in _normalize_text(b.get("title", "")) or term in _normalize_text(b.get("category_name", "")) for term in excluded_terms)
            and b.get("stock", 0) > 0
        ]
        
        # Return up to 4 books from different categories
        return filtered[:4]
    except Exception:
        return []


def _build_rag_answer(question, customer_id=None):
    normalized = _normalize_text(question)

    complaint_keywords = [
        "ghet",
        "that vong",
        "khong hai long",
        "bo di",
        "roi bo",
        "te",
        "xau",
        "uc che",
        "khong thich",
    ]
    purchase_keywords = [
        "mua",
        "sach",
        "goi y",
        "de xuat",
        "nen chon",
        "chon gi",
        "gioi thieu",
    ]
    positive_keywords = [
        "thich",
        "hay",
        "tuyet",
        "hai long",
        "yeu",
        "rat tot",
    ]

    is_complaint = any(keyword in normalized for keyword in complaint_keywords)
    is_purchase = any(keyword in normalized for keyword in purchase_keywords)
    is_positive = any(keyword in normalized for keyword in positive_keywords)
    
    recommended_books = []

    if is_complaint:
        import re

        topic = _extract_topic_from_question(question)
        quoted = re.findall(r'"([^"]+)"', question)
        excluded_title = quoted[0].strip() if quoted else None
        excluded_terms = _extract_complaint_exclusion_terms(question)
        answer = (
            "Khách đang không hài lòng, nên xin lỗi chủ động, ghi nhận góp ý và đề xuất phương án hỗ trợ ngay. "
            "Đồng thời, có thể gợi ý vài sách ở chủ đề khác để khách đổi gu đọc nếu họ muốn."
        )
        if topic:
            recommended_books = _fetch_other_category_books(topic, excluded_title, excluded_terms)
        else:
            try:
                books_res = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
                if books_res.status_code == 200:
                    books = books_res.json()
                    if isinstance(books, list):
                        recommended_books = [
                            b for b in books
                            if b.get("stock", 0) > 0
                            and _normalize_text(b.get("title", "")) != _normalize_text(excluded_title or "")
                            and not any(term in _normalize_text(b.get("title", "")) or term in _normalize_text(b.get("category_name", "")) for term in excluded_terms)
                        ][:4]
            except Exception:
                recommended_books = []

    elif is_positive and is_purchase:
        answer = (
            "Khách đang phản hồi tích cực và muốn mua thêm, nên gợi ý thêm 1-2 cuốn cùng chủ đề, ưu tiên sách top-rated hoặc bản mới nổi bật. "
            "Có thể mở rộng sang các chủ đề gần liên quan để tăng giá trị đơn hàng."
        )
        topic = _extract_topic_from_question(question)
        # Upsell flow: same-topic first, then nearby categories.
        recommended_books = _recommend_books_for_question(
            question,
            focus_category=topic,
            max_items=4,
            allow_related=True,
            customer_id=customer_id,
        )
        seed_category = topic or (recommended_books[0].get("category_name") if recommended_books else None)
        if seed_category:
            existing_ids = {book.get("id") for book in recommended_books}
            for related_category in _related_categories_for(seed_category):
                for book in _fetch_books_by_category(related_category):
                    if book.get("id") in existing_ids:
                        continue
                    recommended_books.append(book)
                    existing_ids.add(book.get("id"))
                    if len(recommended_books) >= 4:
                        break
                if len(recommended_books) >= 4:
                    break

    elif is_purchase:
        topic = _extract_topic_from_question(question)
        if not topic:
            normalized_question = _normalize_text(question)
            if "dev" in normalized_question:
                topic = "DevOps"
        
        if is_positive:
            answer = (
                "Khách đang có tín hiệu tích cực, nên gợi ý thêm 1-2 cuốn cùng chủ đề, ưu tiên sách top-rated hoặc bản mới nổi bật. "
                "Nếu muốn tăng giá trị đơn hàng, có thể ghép thêm combo nhỏ.")
        else:
            answer = (
                "Khách đang muốn mua sách, nên gợi ý 1-2 tựa dễ đọc, cùng chủ đề và có đánh giá cao. "
                "Nếu chưa chắc gu đọc, nên hỏi thêm thể loại, độ dài và mức độ chuyên sâu mong muốn."
            )
        
        # Same-topic / same-title ranking, with a generic fallback when needed.
        recommended_books = _recommend_books_for_question(
            question,
            focus_category=topic,
            max_items=4,
            allow_related=False,
            customer_id=customer_id,
        )
        if topic:
            topic_norm = _normalize_text(topic)
            recommended_books = [
                b for b in (recommended_books or [])
                if _normalize_text(b.get("category_name", "")) == topic_norm
            ]
            if not recommended_books:
                recommended_books = _fetch_books_by_category(topic)
        if not recommended_books:
            recommended_books = _recommend_books_for_question(
                question,
                focus_category=None,
                max_items=4,
                allow_related=False,
                customer_id=customer_id,
            )

    elif is_positive:
        answer = (
            "Khách đang phản hồi tích cực, có thể ghi nhận cảm xúc tốt và gợi ý thêm sách cùng chủ đề để tăng giá trị đơn hàng. "
            "Có thể đề xuất phiên bản mới, bộ sưu tập liên quan hoặc combo nhẹ."
        )
        topic = _extract_topic_from_question(question)
        # Same-topic plus near-related categories for upsell.
        recommended_books = _recommend_books_for_question(
            question,
            focus_category=topic,
            max_items=4,
            allow_related=True,
            customer_id=customer_id,
        )
        seed_category = topic or (recommended_books[0].get("category_name") if recommended_books else None)
        if seed_category:
            existing_ids = {book.get("id") for book in recommended_books}
            for related_category in _related_categories_for(seed_category):
                for book in _fetch_books_by_category(related_category):
                    if book.get("id") in existing_ids:
                        continue
                    recommended_books.append(book)
                    existing_ids.add(book.get("id"))
                    if len(recommended_books) >= 4:
                        break
                if len(recommended_books) >= 4:
                    break
        if not recommended_books:
            recommended_books = _recommend_books_for_question(
                question,
                focus_category=None,
                max_items=4,
                allow_related=True,
                customer_id=customer_id,
            )

    elif customer_id is not None:
        answer = (
            "Khách này nên được tư vấn theo nhu cầu hiện tại và lịch sử mua gần đây. "
            "Hãy hỏi thêm khách đang thích chủ đề nào, cần sách dễ đọc hay chuyên sâu, rồi mới chốt gợi ý phù hợp."
        )
    else:
        answer = "Hãy nói rõ khách đang muốn mua gì, thích chủ đề nào hoặc đang gặp vấn đề gì để mình tư vấn đúng hơn."
    
    return {"answer": answer, "recommended_books": (recommended_books or [])[:4]}


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

def store_reviews(request):
    return render(request, "store/store_reviews.html")

def store_ai_advisor(request):
    return render(request, "store/store_ai_advisor.html")

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

    normalized_path = (path or "").rstrip("/")
    if service == "reviews" and normalized_path == "rag/chat" and request.method == "POST":
        try:
            body = json.loads(request.body or b"{}")
        except Exception:
            body = {}

        question = body.get("question", "")
        customer_id = body.get("customer_id")
        rag_result = _build_rag_answer(question, customer_id)
        response = {
            "question": question,
            "customer_id": customer_id,
            "answer": rag_result.get("answer", ""),
            "recommended_books": rag_result.get("recommended_books", []),
            "retrieved_chunks": [],
            "behavior_context": {"found": False, "message": "Gateway-generated concise advisory response."},
            "model": "Gateway-RAG-Rules",
        }
        _log_request(request_id, request, f"gateway://reviews/{path}", 200, started_at)
        return _with_request_id(JsonResponse(response, status=200), request_id)

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
