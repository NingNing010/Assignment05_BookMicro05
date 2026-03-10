"""
AI Agent for BookStore Customer Service.

This agent processes natural language commands from customers and
automatically performs actions across microservices:
- Search/browse books (book-service)
- Manage cart: add, view, update (cart-service)
- Place orders (order-service)
- Rate/review books (comment-rate-service)
- Get recommendations (recommender-ai-service)
- Register as customer (customer-service local)
"""

import re
import unicodedata
import requests
import logging

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Service URLs (Docker internal network)
# ──────────────────────────────────────────────
BOOK_SERVICE_URL = "http://book-service:8000"
CART_SERVICE_URL = "http://cart-service:8000"
ORDER_SERVICE_URL = "http://order-service:8000"
COMMENT_RATE_SERVICE_URL = "http://comment-rate-service:8000"
RECOMMENDER_SERVICE_URL = "http://recommender-ai-service:8000"

# For local dev without Docker, override these:
# BOOK_SERVICE_URL = "http://localhost:8002"
# CART_SERVICE_URL = "http://localhost:8003"
# ORDER_SERVICE_URL = "http://localhost:8007"
# COMMENT_RATE_SERVICE_URL = "http://localhost:8010"
# RECOMMENDER_SERVICE_URL = "http://localhost:8011"


def safe_request(method, url, **kwargs):
    """Make HTTP request with error handling."""
    try:
        r = getattr(requests, method)(url, timeout=10, **kwargs)
        r.raise_for_status()
        return {"success": True, "data": r.json()}
    except requests.ConnectionError:
        return {"success": False, "error": f"Cannot connect to {url}. Is the service running?"}
    except requests.Timeout:
        return {"success": False, "error": f"Request to {url} timed out."}
    except requests.HTTPError as e:
        return {"success": False, "error": f"HTTP error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ══════════════════════════════════════════════
# TOOL FUNCTIONS — each wraps one microservice call
# ══════════════════════════════════════════════

def tool_search_books(query=None):
    """Search / list all books. Optionally filter by title or author keyword."""
    result = safe_request("get", f"{BOOK_SERVICE_URL}/books/")
    if not result["success"]:
        return result

    books = result["data"]
    if query:
        q = query.lower()
        books = [
            b for b in books
            if q in b.get("title", "").lower() or q in b.get("author", "").lower()
        ]

    if not books:
        return {"success": True, "message": f"No books found matching '{query}'." if query else "No books available.", "books": []}

    return {
        "success": True,
        "message": f"Found {len(books)} book(s).",
        "books": books,
    }


def tool_view_cart(customer_id):
    """View the customer's current cart."""
    result = safe_request("get", f"{CART_SERVICE_URL}/carts/{customer_id}/")
    if not result["success"]:
        return result
    items = result["data"]
    if not items:
        return {"success": True, "message": "Your cart is empty.", "items": []}
    return {
        "success": True,
        "message": f"You have {len(items)} item(s) in your cart.",
        "items": items,
    }


def tool_add_to_cart(customer_id, book_id, quantity=1):
    """Add a book to the customer's cart."""
    # First get the cart for this customer
    cart_result = safe_request("get", f"{CART_SERVICE_URL}/carts/{customer_id}/")

    # We need the cart ID — get all carts or try to find it
    # The cart was auto-created when customer registered
    # We'll post directly with cart lookup
    result = safe_request("post", f"{CART_SERVICE_URL}/cart-items/", json={
        "cart": customer_id,  # cart ID typically matches sequence
        "book_id": book_id,
        "quantity": quantity,
    })
    if not result["success"]:
        return result
    return {
        "success": True,
        "message": f"Added book #{book_id} (qty: {quantity}) to your cart.",
        "item": result["data"],
    }


def tool_place_order(customer_id, payment_method="credit_card", shipping_method="standard"):
    """Place an order from current cart contents."""
    result = safe_request("post", f"{ORDER_SERVICE_URL}/orders/", json={
        "customer_id": customer_id,
        "payment_method": payment_method,
        "shipping_method": shipping_method,
    })
    if not result["success"]:
        return result
    return {
        "success": True,
        "message": f"Order placed successfully! Order #{result['data'].get('id', '?')} — Status: {result['data'].get('status', 'pending')}",
        "order": result["data"],
    }


def tool_view_orders(customer_id):
    """View all orders for a customer."""
    result = safe_request("get", f"{ORDER_SERVICE_URL}/orders/")
    if not result["success"]:
        return result
    orders = [o for o in result["data"] if o.get("customer_id") == customer_id]
    if not orders:
        return {"success": True, "message": "You have no orders yet.", "orders": []}
    return {
        "success": True,
        "message": f"You have {len(orders)} order(s).",
        "orders": orders,
    }


def tool_rate_book(customer_id, book_id, rating, comment=""):
    """Rate and review a book."""
    if not 1 <= rating <= 5:
        return {"success": False, "error": "Rating must be between 1 and 5."}
    result = safe_request("post", f"{COMMENT_RATE_SERVICE_URL}/reviews/", json={
        "customer_id": customer_id,
        "book_id": book_id,
        "rating": rating,
        "comment": comment,
    })
    if not result["success"]:
        return result
    return {
        "success": True,
        "message": f"Thanks! You rated book #{book_id} with {rating}/5 stars.",
        "review": result["data"],
    }


def tool_get_reviews(book_id):
    """Get all reviews for a specific book."""
    result = safe_request("get", f"{COMMENT_RATE_SERVICE_URL}/reviews/book/{book_id}/")
    if not result["success"]:
        return result
    reviews = result["data"]
    if not reviews:
        return {"success": True, "message": f"No reviews yet for book #{book_id}.", "reviews": []}
    avg = sum(r.get("rating", 0) for r in reviews) / len(reviews)
    return {
        "success": True,
        "message": f"Book #{book_id} has {len(reviews)} review(s), avg rating: {avg:.1f}/5.",
        "reviews": reviews,
        "average_rating": round(avg, 1),
    }


def tool_get_recommendations(customer_id):
    """Get AI book recommendations for the customer."""
    result = safe_request("get", f"{RECOMMENDER_SERVICE_URL}/recommendations/{customer_id}/")
    if not result["success"]:
        return result
    recs = result["data"]
    if not recs:
        return {"success": True, "message": "No recommendations available yet. Try rating some books first!", "recommendations": []}
    return {
        "success": True,
        "message": f"Here are {len(recs)} recommended book(s) for you!",
        "recommendations": recs,
    }


def tool_update_book_price(book_id, price):
    """Update the price of a book."""
    result = safe_request("patch", f"{BOOK_SERVICE_URL}/books/{book_id}/", json={"price": str(price)})
    if not result["success"]:
        return result
    return {
        "success": True,
        "message": f"Book #{book_id} price updated to ${price}.",
        "book": result["data"],
    }


def tool_remove_cart_item(item_id):
    """Remove an item from the cart."""
    result = safe_request("delete", f"{CART_SERVICE_URL}/cart-items/{item_id}/")
    if not result["success"]:
        return result
    return {"success": True, "message": f"Cart item #{item_id} removed."}


def tool_clear_cart(customer_id):
    """Clear all items from the customer's cart."""
    result = safe_request("delete", f"{CART_SERVICE_URL}/carts/{customer_id}/")
    if not result["success"]:
        return result
    return {"success": True, "message": "Your cart has been cleared."}


def tool_cancel_order(order_id):
    """Cancel an order."""
    result = safe_request("delete", f"{ORDER_SERVICE_URL}/orders/{order_id}/")
    if not result["success"]:
        return result
    return {
        "success": True,
        "message": f"Order #{order_id} has been cancelled.",
    }


def tool_view_book(book_id):
    """View details of a single book."""
    result = safe_request("get", f"{BOOK_SERVICE_URL}/books/{book_id}/")
    if not result["success"]:
        return result
    return {
        "success": True,
        "message": f"Book #{book_id}: {result['data'].get('title', '')} by {result['data'].get('author', '')} — ${result['data'].get('price', '?')}",
        "book": result["data"],
    }


# ══════════════════════════════════════════════
# INTENT PARSER — maps natural language to tools
# ══════════════════════════════════════════════

INTENT_PATTERNS = [
    # Search books
    (r"(?:search|find|look\s*(?:for|up)?|browse|show|list|what)\s*(?:all\s+)?books?(?:\s+(?:about|by|titled?|named?|called|with|on))?\s*(.*)?",
     "search_books"),
    (r"(?:tìm|tìm\s*kiếm|xem|hiện|danh\s*sách)\s*(?:tất\s*cả\s+)?sách\s*(.*)?",
     "search_books"),

    # Update book price (must be before view_book)
    (r"(?:update|change|set)\s+(?:book\s*)?#?(\d+)\s+price\s+(?:to\s+)?\$?(\d+\.?\d*)",
     "update_book_price"),
    (r"(?:cập\s*nhật|đổi|sửa)\s+(?:giá\s+)?(?:sách\s*)?#?(\d+)\s+(?:giá\s+)?(\d+\.?\d*)",
     "update_book_price"),

    # Rate book (must be before view_book)
    (r"(?:rate|review)\s+(?:book\s*)?#?(\d+)\s+(\d)\s*(?:stars?|/5)?(?:\s+(.+))?",
     "rate_book"),
    (r"(?:đánh\s*giá|rate)\s+(?:sách\s*)?#?(\d+)\s+(\d)\s*(?:sao)?(?:\s+(.+))?",
     "rate_book"),

    # Get reviews (must be before view_book)
    (r"(?:reviews?|ratings?)\s+(?:for\s+|of\s+)?(?:book\s*)?#?(\d+)",
     "get_reviews"),
    (r"(?:đánh\s*giá|review)\s+(?:của\s+)?(?:sách\s*)?#?(\d+)",
     "get_reviews"),

    # Add to cart (must be before view_book)
    (r"(?:add|put)\s+(?:book\s*)?#?(\d+)\s+(?:to\s+)?(?:my\s+)?cart(?:\s+(?:qty|quantity|x)\s*(\d+))?",
     "add_to_cart"),
    (r"(?:thêm|bỏ)\s+(?:sách\s*)?#?(\d+)\s+(?:vào\s+)?giỏ(?:\s+(?:sl|số\s*lượng)\s*(\d+))?",
     "add_to_cart"),

    # View single book detail (only match standalone "book #N" or "detail #N")
    (r"^(?:book|detail|info)\s*#?(\d+)$",
     "view_book"),
    (r"^(?:chi\s*tiết|thông\s*tin)\s*(?:sách\s*)?#?(\d+)$",
     "view_book"),

    # Remove cart item
    (r"(?:remove|delete)\s+(?:cart\s*)?item\s*#?(\d+)(?:\s+from\s+cart)?",
     "remove_cart_item"),
    (r"(?:xóa|bỏ)\s+(?:item|mục)\s*#?(\d+)\s*(?:khỏi\s+giỏ)?",
     "remove_cart_item"),

    # Clear cart
    (r"(?:clear|empty)\s+(?:my\s+)?cart",
     "clear_cart"),
    (r"(?:xóa\s*hết|làm\s*trống)\s+giỏ\s*(?:hàng)?",
     "clear_cart"),

    # View cart
    (r"(?:view|show|see|check|open)\s+(?:my\s+)?cart",
     "view_cart"),
    (r"(?:xem|mở|kiểm\s*tra)\s+giỏ\s*(?:hàng)?",
     "view_cart"),

    # Place order
    (r"(?:place|create|make|submit)\s+(?:an?\s+)?order(?:\s+(?:pay\s+(?:by|with)\s+(\w+))?(?:\s+ship\s+(?:by|with)\s+(\w+))?)?",
     "place_order"),
    (r"(?:đặt|tạo)\s+(?:đơn\s*)?hàng(?:\s+(?:thanh\s*toán\s+(\w+))?(?:\s+giao\s+(\w+))?)?",
     "place_order"),

    # Cancel order
    (r"(?:cancel|delete)\s+order\s*#?(\d+)",
     "cancel_order"),
    (r"(?:hủy|xóa)\s+(?:đơn\s*(?:hàng)?\s*)?#?(\d+)",
     "cancel_order"),

    # View orders
    (r"(?:view|show|see|check|my)\s+orders?",
     "view_orders"),
    (r"(?:xem|kiểm\s*tra)\s+(?:đơn\s*)?hàng(?:\s+của\s+tôi)?",
     "view_orders"),

    # Recommendations
    (r"(?:recommend|suggest|what\s+should\s+I\s+read)",
     "get_recommendations"),
    (r"(?:gợi\s*ý|đề\s*xuất|nên\s+đọc\s+gì)",
     "get_recommendations"),

    # Help
    (r"(?:help|commands|what\s+can\s+you\s+do|\?)",
     "help"),
    (r"(?:giúp|trợ\s*giúp|hướng\s*dẫn|lệnh)",
     "help"),
]


def _remove_diacritics(text):
    """Remove Vietnamese diacritics so unaccented input matches accented patterns."""
    nfkd = unicodedata.normalize('NFD', text)
    stripped = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return stripped.replace('đ', 'd').replace('Đ', 'D')


def parse_intent(message):
    """Parse a natural language message into an intent + params."""
    text = message.strip()
    # First pass — original text
    for pattern, intent in INTENT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return intent, match.groups()
    # Second pass — diacritics removed (handles unaccented Vietnamese)
    norm_text = _remove_diacritics(text)
    for pattern, intent in INTENT_PATTERNS:
        norm_pattern = _remove_diacritics(pattern)
        match = re.search(norm_pattern, norm_text, re.IGNORECASE)
        if match:
            return intent, match.groups()
    return "unknown", ()


# ══════════════════════════════════════════════
# AGENT — orchestrates parsing + tool execution
# ══════════════════════════════════════════════

HELP_TEXT = """🤖 **BookStore AI Agent** — I can help you with:

📚 **Search books**: "search books about Python" / "tìm sách Python"
� **Book detail**: "book #1" / "chi tiết sách #1"
💰 **Update price**: "update book #1 price to 29.99" / "cập nhật sách #1 giá 29.99"
🛒 **Add to cart**: "add book #3 to cart" / "thêm sách #3 vào giỏ"
🛒 **View cart**: "view my cart" / "xem giỏ hàng"
🗑️ **Remove item**: "remove item #1 from cart" / "xóa item #1 khỏi giỏ"
🧹 **Clear cart**: "clear cart" / "xóa hết giỏ hàng"
📦 **Place order**: "place order" / "đặt hàng"
❌ **Cancel order**: "cancel order #1" / "hủy đơn #1"
📋 **View orders**: "view my orders" / "xem đơn hàng"
⭐ **Rate a book**: "rate book #2 5 stars Great!" / "đánh giá sách #2 5 sao"
💬 **Book reviews**: "reviews for book #1" / "đánh giá sách #1"
🎯 **Recommendations**: "recommend" / "gợi ý sách"
❓ **Help**: "help" / "giúp"

I understand both English and Vietnamese! 🇺🇸🇻🇳
"""


class BookStoreAgent:
    """
    AI Agent that processes customer commands via natural language
    and orchestrates actions across BookStore microservices.
    """

    def __init__(self, customer_id):
        self.customer_id = customer_id
        self.conversation_history = []

    def process(self, message):
        """
        Process a natural language message from the customer.
        Returns a structured response with message + data.
        """
        self.conversation_history.append({"role": "user", "content": message})

        intent, params = parse_intent(message)
        response = self._execute_intent(intent, params)

        self.conversation_history.append({"role": "agent", "content": response.get("message", "")})
        response["intent"] = intent
        return response

    def _execute_intent(self, intent, params):
        """Route intent to the appropriate tool function."""

        if intent == "help":
            return {"success": True, "message": HELP_TEXT}

        elif intent == "search_books":
            query = params[0].strip() if params and params[0] else None
            return tool_search_books(query)

        elif intent == "view_book":
            book_id = int(params[0]) if params[0] else None
            if not book_id:
                return {"success": False, "message": "Please specify a book ID. Example: 'book #1'"}
            return tool_view_book(book_id)

        elif intent == "update_book_price":
            book_id = int(params[0]) if params[0] else None
            price = float(params[1]) if (len(params) > 1 and params[1]) else None
            if not book_id or price is None:
                return {"success": False, "message": "Please specify book ID and price. Example: 'update book #1 price to 29.99'"}
            return tool_update_book_price(book_id, price)

        elif intent == "view_cart":
            return tool_view_cart(self.customer_id)

        elif intent == "add_to_cart":
            book_id = int(params[0]) if params[0] else None
            quantity = int(params[1]) if (len(params) > 1 and params[1]) else 1
            if not book_id:
                return {"success": False, "message": "Please specify a book ID. Example: 'add book #3 to cart'"}
            return tool_add_to_cart(self.customer_id, book_id, quantity)

        elif intent == "remove_cart_item":
            item_id = int(params[0]) if params[0] else None
            if not item_id:
                return {"success": False, "message": "Please specify item ID. Example: 'remove item #1 from cart'"}
            return tool_remove_cart_item(item_id)

        elif intent == "clear_cart":
            return tool_clear_cart(self.customer_id)

        elif intent == "place_order":
            payment = params[0] if (params and params[0]) else "credit_card"
            shipping = params[1] if (len(params) > 1 and params[1]) else "standard"
            return tool_place_order(self.customer_id, payment, shipping)

        elif intent == "cancel_order":
            order_id = int(params[0]) if params[0] else None
            if not order_id:
                return {"success": False, "message": "Please specify order ID. Example: 'cancel order #1'"}
            return tool_cancel_order(order_id)

        elif intent == "view_orders":
            return tool_view_orders(self.customer_id)

        elif intent == "rate_book":
            book_id = int(params[0]) if params[0] else None
            rating = int(params[1]) if (len(params) > 1 and params[1]) else None
            comment = params[2].strip() if (len(params) > 2 and params[2]) else ""
            if not book_id or not rating:
                return {"success": False, "message": "Please specify book ID and rating. Example: 'rate book #2 5 stars Great book!'"}
            return tool_rate_book(self.customer_id, book_id, rating, comment)

        elif intent == "get_reviews":
            book_id = int(params[0]) if params[0] else None
            if not book_id:
                return {"success": False, "message": "Please specify a book ID. Example: 'reviews for book #1'"}
            return tool_get_reviews(book_id)

        elif intent == "get_recommendations":
            return tool_get_recommendations(self.customer_id)

        else:
            return {
                "success": False,
                "message": f"I didn't understand '{intent}'. Type 'help' to see what I can do!",
            }
