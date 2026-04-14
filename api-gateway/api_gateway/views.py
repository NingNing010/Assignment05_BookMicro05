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
import random
import jwt
import unicodedata

PRODUCT_SERVICE_URL = "http://product-service:8000"  # DDD — replaces book/clothes/catalog
CART_SERVICE_URL = "http://cart-service:8000"
CUSTOMER_SERVICE_URL = "http://customer-service:8000"
STAFF_SERVICE_URL = "http://staff-service:8000"
ORDER_SERVICE_URL = "http://order-service:8000"
PAY_SERVICE_URL = "http://pay-service:8000"
SHIP_SERVICE_URL = "http://ship-service:8000"
COMMENT_RATE_SERVICE_URL = "http://comment-rate-service:8000"
RECOMMENDER_SERVICE_URL = "http://recommender-ai-service:8000"
MANAGER_SERVICE_URL = "http://manager-service:8000"
AUTH_SERVICE_URL = "http://auth-service:8000"

JWT_SECRET = os.getenv("JWT_SECRET", "bookstore-jwt-secret")
JWT_ALGORITHM = "HS256"

RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_DEFAULT = int(os.getenv("RATE_LIMIT_DEFAULT", "3000"))
RATE_LIMIT_GUEST = int(os.getenv("RATE_LIMIT_GUEST", "1000"))
RATE_LIMIT_ADMIN = int(os.getenv("RATE_LIMIT_ADMIN", "5000"))

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
    'books': PRODUCT_SERVICE_URL,
    'publishers': PRODUCT_SERVICE_URL,
    'categories': PRODUCT_SERVICE_URL,
    'products': PRODUCT_SERVICE_URL,
    'clothes': PRODUCT_SERVICE_URL,
    'brands': PRODUCT_SERVICE_URL,
    'product-types': PRODUCT_SERVICE_URL,
    'variants': PRODUCT_SERVICE_URL,
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


# ══════════════════════════════════════════════════════════════════════════════
# AI ENGINE — Graph Knowledge Base + FAISS Vector Search + RAG Pipeline
# Architecture based on professor's specification:
#   1. Graph Knowledge Base (heterogeneous graph: User, Product, Category, Query)
#   2. Deep Learning for Behavior Analysis (weighted behavior scoring)
#   3. RAG Chat (Retrieve from Graph + Vector → Build Context → Generate)
# ══════════════════════════════════════════════════════════════════════════════


from collections import defaultdict
import math
import threading

# ── 1. GRAPH KNOWLEDGE BASE ──────────────────────────────────────────────────
# Heterogeneous graph with nodes: User, Product, Category, Query
# Edges: viewed, carted, purchased, searched, belongs_to, similar

class GraphKnowledgeBase:
    """In-memory Knowledge Graph for e-commerce AI.
    
    Nodes: User(U), Product(P), Category(C), Query(Q)
    Edges: U→P (viewed/carted/purchased), U→Q (searched), P→C (belongs_to), P↔P (similar)
    
    Weighted edges: w(u,p) = α·views + β·carts + γ·purchases
    """
    
    _instance = None
    _lock = threading.Lock()
    
    ALPHA = 1.0   # view weight
    BETA = 3.0    # cart weight  
    GAMMA = 5.0   # purchase weight
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        # Adjacency lists for each edge type
        self.user_product_views = defaultdict(lambda: defaultdict(int))     # U→P: view count
        self.user_product_carts = defaultdict(lambda: defaultdict(int))     # U→P: cart count
        self.user_product_purchases = defaultdict(lambda: defaultdict(int)) # U→P: purchase count
        self.user_queries = defaultdict(list)                               # U→Q: search queries
        self.product_category = {}                                          # P→C: belongs_to
        self.product_info = {}                                              # P metadata cache
        self.category_products = defaultdict(set)                           # C→P reverse index
        self.query_products = defaultdict(set)                              # Q→P: query-product association
        self._initialized = False
    
    def log_interaction(self, user_id, product_id, event_type, query_text=None):
        """Log a user-product interaction into the graph."""
        if event_type == 'view':
            self.user_product_views[user_id][product_id] += 1
        elif event_type == 'cart':
            self.user_product_carts[user_id][product_id] += 1
        elif event_type == 'purchase':
            self.user_product_purchases[user_id][product_id] += 1
        elif event_type == 'search' and query_text:
            self.user_queries[user_id].append({
                'query': query_text,
                'timestamp': time.time()
            })
            if product_id:
                self.query_products[_normalize_text(query_text)].add(product_id)
    
    def get_user_interest_score(self, user_id, product_id):
        """Calculate weighted interest: w(u,p) = α·views + β·carts + γ·purchases"""
        views = self.user_product_views.get(user_id, {}).get(product_id, 0)
        carts = self.user_product_carts.get(user_id, {}).get(product_id, 0)
        purchases = self.user_product_purchases.get(user_id, {}).get(product_id, 0)
        return self.ALPHA * views + self.BETA * carts + self.GAMMA * purchases
    
    def get_user_top_products(self, user_id, limit=10):
        """Get top products for a user by weighted interest score."""
        scores = {}
        for pid in set(
            list(self.user_product_views.get(user_id, {}).keys()) +
            list(self.user_product_carts.get(user_id, {}).keys()) +
            list(self.user_product_purchases.get(user_id, {}).keys())
        ):
            scores[pid] = self.get_user_interest_score(user_id, pid)
        sorted_products = sorted(scores.items(), key=lambda x: -x[1])
        return sorted_products[:limit]
    
    def get_user_preferred_categories(self, user_id):
        """Get user's preferred categories from interaction history."""
        category_scores = defaultdict(float)
        for pid, score in self.get_user_top_products(user_id, 50):
            cat = self.product_category.get(pid)
            if cat:
                category_scores[cat] += score
        return sorted(category_scores.items(), key=lambda x: -x[1])
    
    def get_similar_users(self, user_id, limit=5):
        """Find users with similar behavior (co-viewed/co-purchased products)."""
        my_products = set(self.user_product_views.get(user_id, {}).keys())
        my_products |= set(self.user_product_purchases.get(user_id, {}).keys())
        if not my_products:
            return []
        
        user_overlap = {}
        for other_uid in self.user_product_views:
            if other_uid == user_id:
                continue
            other_products = set(self.user_product_views[other_uid].keys())
            other_products |= set(self.user_product_purchases.get(other_uid, {}).keys())
            overlap = len(my_products & other_products)
            if overlap > 0:
                user_overlap[other_uid] = overlap
        
        return sorted(user_overlap.items(), key=lambda x: -x[1])[:limit]
    
    def get_collaborative_recommendations(self, user_id, limit=10):
        """Recommend products that similar users interacted with but this user hasn't."""
        my_products = set(self.user_product_views.get(user_id, {}).keys())
        my_products |= set(self.user_product_purchases.get(user_id, {}).keys())
        
        recommendations = defaultdict(float)
        for other_uid, overlap_score in self.get_similar_users(user_id, 10):
            for pid in self.user_product_purchases.get(other_uid, {}):
                if pid not in my_products:
                    recommendations[pid] += overlap_score * self.GAMMA
            for pid in self.user_product_carts.get(other_uid, {}):
                if pid not in my_products:
                    recommendations[pid] += overlap_score * self.BETA
        
        return sorted(recommendations.items(), key=lambda x: -x[1])[:limit]
    
    def build_from_services(self):
        """Populate graph from existing service data (orders, reviews)."""
        if self._initialized:
            return
        
        # Load products into graph
        try:
            res = requests.get(f"{PRODUCT_SERVICE_URL}/products/", timeout=8)
            if res.status_code == 200:
                products = res.json()
                if isinstance(products, list):
                    for p in products:
                        pid = p.get('id')
                        self.product_info[pid] = p
                        cat = p.get('category_name', '')
                        if cat:
                            self.product_category[pid] = cat
                            self.category_products[cat].add(pid)
        except Exception:
            pass
        
        # Load orders → purchase edges
        try:
            res = requests.get(f"{ORDER_SERVICE_URL}/orders/", timeout=8)
            if res.status_code == 200:
                orders = res.json()
                if isinstance(orders, list):
                    for order in orders:
                        uid = order.get('customer_id')
                        if not uid:
                            continue
                        for item in (order.get('items') or []):
                            pid = item.get('book_id') or item.get('product_id')
                            if pid:
                                self.user_product_purchases[uid][pid] += 1
        except Exception:
            pass
        
        # Load reviews → view edges (if a user reviewed, they viewed it)
        try:
            res = requests.get(f"{COMMENT_RATE_SERVICE_URL}/reviews/", timeout=8)
            if res.status_code == 200:
                reviews = res.json()
                if isinstance(reviews, list):
                    for r in reviews:
                        uid = r.get('customer_id')
                        pid = r.get('book_id') or r.get('product_id')
                        if uid and pid:
                            self.user_product_views[uid][pid] += 1
        except Exception:
            pass
        
        self._initialized = True
    
    def get_behavior_summary(self, user_id):
        """Generate human-readable behavior summary for RAG context."""
        top_products = self.get_user_top_products(user_id, 5)
        pref_categories = self.get_user_preferred_categories(user_id)
        
        parts = []
        if top_products:
            names = []
            for pid, score in top_products[:3]:
                info = self.product_info.get(pid, {})
                names.append(info.get('name', f'Product#{pid}'))
            parts.append(f"Đã tương tác nhiều nhất với: {', '.join(names)}")
        
        if pref_categories:
            cats = [cat for cat, _ in pref_categories[:3]]
            parts.append(f"Danh mục yêu thích: {', '.join(cats)}")
        
        queries = self.user_queries.get(user_id, [])
        if queries:
            recent = [q['query'] for q in queries[-3:]]
            parts.append(f"Tìm kiếm gần đây: {', '.join(recent)}")
        
        return "; ".join(parts) if parts else "Chưa có dữ liệu hành vi."


# ── 2. VECTOR STORE (FAISS-like TF-IDF) ─────────────────────────────────────
# Product embeddings using TF-IDF vectors for similarity search

class VectorStore:
    """TF-IDF based vector store for product similarity search.
    Similar to FAISS but uses pure Python for zero-dependency deployment.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.documents = []      # [{id, text, product}]
        self.vocabulary = {}     # term → index
        self.idf = {}           # term → idf score
        self.tfidf_matrix = []  # list of sparse vectors
        self._built = False
    
    def _tokenize(self, text):
        text = _normalize_text(text)
        tokens = re.findall(r'[a-z0-9]+', text)
        return [t for t in tokens if len(t) >= 2]
    
    def _compute_tf(self, tokens):
        tf = defaultdict(int)
        for t in tokens:
            tf[t] += 1
        total = len(tokens) or 1
        return {t: count / total for t, count in tf.items()}
    
    def build_index(self, products):
        """Build TF-IDF index from product list."""
        if self._built:
            return
        
        self.documents = []
        all_tokens_per_doc = []
        
        for p in products:
            text_parts = [
                p.get('name', ''),
                p.get('description', ''),
                p.get('category_name', ''),
                p.get('brand_name', ''),
            ]
            attrs = p.get('attributes', {})
            if isinstance(attrs, dict):
                text_parts.extend([str(v) for v in attrs.values()])
            
            full_text = ' '.join(text_parts)
            tokens = self._tokenize(full_text)
            
            self.documents.append({
                'id': p.get('id'),
                'text': full_text,
                'product': p,
                'tokens': tokens,
            })
            all_tokens_per_doc.append(set(tokens))
        
        # Build vocabulary
        vocab = set()
        for tokens in all_tokens_per_doc:
            vocab |= tokens
        self.vocabulary = {term: idx for idx, term in enumerate(sorted(vocab))}
        
        # Compute IDF
        N = len(self.documents) or 1
        for term in self.vocabulary:
            df = sum(1 for doc_tokens in all_tokens_per_doc if term in doc_tokens)
            self.idf[term] = math.log((N + 1) / (df + 1)) + 1
        
        # Compute TF-IDF vectors
        self.tfidf_matrix = []
        for doc in self.documents:
            tf = self._compute_tf(doc['tokens'])
            vector = {}
            for term, tf_val in tf.items():
                if term in self.vocabulary:
                    vector[self.vocabulary[term]] = tf_val * self.idf.get(term, 1)
            self.tfidf_matrix.append(vector)
        
        self._built = True
    
    def _cosine_similarity(self, vec1, vec2):
        """Compute cosine similarity between two sparse vectors."""
        common_keys = set(vec1.keys()) & set(vec2.keys())
        if not common_keys:
            return 0.0
        
        dot = sum(vec1[k] * vec2[k] for k in common_keys)
        norm1 = math.sqrt(sum(v * v for v in vec1.values()))
        norm2 = math.sqrt(sum(v * v for v in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
    
    def search(self, query_text, k=10, category_filter=None):
        """Search for similar products using TF-IDF cosine similarity."""
        if not self._built or not self.documents:
            return []
        
        tokens = self._tokenize(query_text)
        tf = self._compute_tf(tokens)
        query_vector = {}
        for term, tf_val in tf.items():
            if term in self.vocabulary:
                query_vector[self.vocabulary[term]] = tf_val * self.idf.get(term, 1)
        
        if not query_vector:
            return []
        
        results = []
        for idx, doc_vector in enumerate(self.tfidf_matrix):
            sim = self._cosine_similarity(query_vector, doc_vector)
            if sim > 0.01:
                product = self.documents[idx]['product']
                if category_filter:
                    if _normalize_text(product.get('category_name', '')) != _normalize_text(category_filter):
                        continue
                results.append((sim, product))
        
        results.sort(key=lambda x: -x[0])
        return results[:k]
    
    def get_similar_products(self, product_id, k=5):
        """Find products similar to a given product."""
        target_idx = None
        for idx, doc in enumerate(self.documents):
            if doc['id'] == product_id:
                target_idx = idx
                break
        
        if target_idx is None:
            return []
        
        target_vector = self.tfidf_matrix[target_idx]
        results = []
        for idx, doc_vector in enumerate(self.tfidf_matrix):
            if idx == target_idx:
                continue
            sim = self._cosine_similarity(target_vector, doc_vector)
            if sim > 0.05:
                results.append((sim, self.documents[idx]['product']))
        
        results.sort(key=lambda x: -x[0])
        return results[:k]


# ── 3. RAG PIPELINE ──────────────────────────────────────────────────────────
# Retrieve (Graph + Vector) → Build Context → Generate Response

def _ensure_ai_initialized():
    """Lazy-initialize Graph and Vector Store from product service data."""
    graph = GraphKnowledgeBase.get_instance()
    vector_store = VectorStore.get_instance()
    
    if not graph._initialized:
        graph.build_from_services()
    
    if not vector_store._built:
        products = list(graph.product_info.values())
        if not products:
            try:
                res = requests.get(f"{PRODUCT_SERVICE_URL}/products/", timeout=8)
                if res.status_code == 200:
                    products = res.json()
                    if isinstance(products, list):
                        for p in products:
                            graph.product_info[p['id']] = p
                            cat = p.get('category_name', '')
                            if cat:
                                graph.product_category[p['id']] = cat
                                graph.category_products[cat].add(p['id'])
            except Exception:
                pass
        vector_store.build_index(products)
    
    return graph, vector_store


def _rag_retrieve(question, user_id=None, graph=None, vector_store=None):
    """RAG Step 1: Retrieve relevant products from Graph + Vector Store."""
    retrieved = []
    retrieved_ids = set()
    
    # 1a. Vector search — semantic similarity  
    vector_results = vector_store.search(question, k=15)
    for score, product in vector_results:
        pid = product.get('id')
        if pid not in retrieved_ids:
            retrieved.append({
                'product': product,
                'score': score * 100,
                'source': 'vector_search'
            })
            retrieved_ids.add(pid)
    
    # 1b. Graph-based retrieval — user behavior
    if user_id:
        # Products the user interacted with
        top_products = graph.get_user_top_products(user_id, 10)
        for pid, interest_score in top_products:
            if pid not in retrieved_ids:
                info = graph.product_info.get(pid)
                if info:
                    retrieved.append({
                        'product': info,
                        'score': interest_score * 10,
                        'source': 'graph_user_history'
                    })
                    retrieved_ids.add(pid)
        
        # Collaborative filtering — similar users' purchases
        collab = graph.get_collaborative_recommendations(user_id, 8)
        for pid, collab_score in collab:
            if pid not in retrieved_ids:
                info = graph.product_info.get(pid)
                if info:
                    retrieved.append({
                        'product': info,
                        'score': collab_score,
                        'source': 'graph_collaborative'
                    })
                    retrieved_ids.add(pid)
    
    # Sort by combined score
    retrieved.sort(key=lambda x: -x['score'])
    return retrieved[:20]


def _rag_build_context(question, user_id, retrieved, graph):
    """RAG Step 2: Build augmented context from retrieved products + user behavior."""
    context_parts = []
    
    # User behavior context
    if user_id:
        behavior = graph.get_behavior_summary(user_id)
        context_parts.append(f"[Hồ sơ khách hàng] {behavior}")
        
        pref_cats = graph.get_user_preferred_categories(user_id)
        if pref_cats:
            context_parts.append(f"[Danh mục ưa thích] {', '.join([c for c, _ in pref_cats[:5]])}")
    
    # Product context from retrieval
    if retrieved:
        product_summaries = []
        for item in retrieved[:8]:
            p = item['product']
            attrs = p.get('attributes', {})
            attr_str = ', '.join([f"{k}: {v}" for k, v in attrs.items()]) if isinstance(attrs, dict) else ''
            summary = f"- {p.get('name')} ({p.get('category_name', 'N/A')}) — {p.get('price')}₫"
            if attr_str:
                summary += f" [{attr_str}]"
            if p.get('stock', 0) < 1:
                summary += " [HẾT HÀNG]"
            product_summaries.append(summary)
        context_parts.append("[Sản phẩm liên quan]\n" + "\n".join(product_summaries))
    
    return "\n\n".join(context_parts)


def _rag_generate(question, context, retrieved, user_id=None):
    """RAG Step 3: Generate response using context-aware rule engine.
    This is a structured response generator. Can be replaced with LLM API later.
    Integration point: Replace this function body with OpenAI/LLaMA call.
    """
    normalized = _normalize_text(question)
    
    # Classify intent
    complaint_kw = ["ghet", "that vong", "khong hai long", "te", "xau", "uc che", "khong thich", "chan"]
    purchase_kw = ["mua", "goi y", "de xuat", "nen chon", "chon gi", "gioi thieu", "recommend", "tim", "can", "muon"]
    positive_kw = ["thich", "hay", "tuyet", "hai long", "yeu", "rat tot", "tot", "dep"]
    compare_kw = ["so sanh", "khac nhau", "nao tot hon", "compare", "vs"]
    
    is_complaint = any(kw in normalized for kw in complaint_kw)
    is_purchase = any(kw in normalized for kw in purchase_kw)
    is_positive = any(kw in normalized for kw in positive_kw)
    is_compare = any(kw in normalized for kw in compare_kw)
    
    # Filter in-stock products for recommendations
    in_stock = [r for r in retrieved if r['product'].get('stock', 0) > 0]
    
    if is_complaint:
        answer = (
            "🔍 **Phân tích hành vi:** Khách hàng đang không hài lòng.\n\n"
            "📋 **Đề xuất hành động:**\n"
            "1. Xin lỗi chủ động và ghi nhận góp ý\n"
            "2. Đề xuất đổi/trả sản phẩm nếu cần\n"
            "3. Gợi ý sản phẩm thay thế phù hợp hơn\n\n"
        )
        if in_stock:
            answer += "🛍️ **Sản phẩm thay thế được đề xuất** (dựa trên phân tích hành vi và vector similarity):"
        recommended = in_stock[:6]
        
    elif is_compare:
        answer = (
            "🔍 **Phân tích so sánh** (dựa trên Knowledge Graph + Vector Similarity):\n\n"
        )
        if len(in_stock) >= 2:
            p1, p2 = in_stock[0]['product'], in_stock[1]['product']
            answer += f"📊 **{p1.get('name')}** vs **{p2.get('name')}**\n"
            answer += f"  - Giá: {p1.get('price')}₫ vs {p2.get('price')}₫\n"
            answer += f"  - Danh mục: {p1.get('category_name', 'N/A')} vs {p2.get('category_name', 'N/A')}\n"
            a1 = p1.get('attributes', {})
            a2 = p2.get('attributes', {})
            all_keys = set(list(a1.keys()) + list(a2.keys()))
            for k in all_keys:
                v1 = a1.get(k, 'N/A')
                v2 = a2.get(k, 'N/A')
                answer += f"  - {k}: {v1} vs {v2}\n"
        answer += "\n🛍️ **Các sản phẩm liên quan:**"
        recommended = in_stock[:6]
        
    elif is_positive and is_purchase:
        answer = (
            "🔍 **Phân tích hành vi:** Khách hàng phản hồi tích cực và muốn mua thêm.\n\n"
            "📋 **Chiến lược upsell:**\n"
            "1. Gợi ý sản phẩm cùng danh mục, ưu tiên đánh giá cao\n"
            "2. Mở rộng sang danh mục liên quan để tăng giá trị đơn hàng\n"
        )
        if user_id:
            behavior = GraphKnowledgeBase.get_instance().get_behavior_summary(user_id)
            answer += f"3. Dựa trên hồ sơ: {behavior}\n"
        answer += "\n🛍️ **Đề xuất sản phẩm** (GraphRAG + Collaborative Filtering):"
        recommended = in_stock[:6]
        
    elif is_purchase:
        answer = (
            "🔍 **Phân tích nhu cầu** (RAG Pipeline: Graph Retrieval + Vector Search):\n\n"
        )
        if user_id:
            behavior = GraphKnowledgeBase.get_instance().get_behavior_summary(user_id)
            answer += f"📊 **Hồ sơ khách hàng:** {behavior}\n\n"
        answer += "🛍️ **Sản phẩm được đề xuất** (dựa trên TF-IDF similarity + behavior scoring):"
        recommended = in_stock[:6]
        
    elif is_positive:
        answer = (
            "🔍 **Phân tích:** Khách hàng đang phản hồi tích cực.\n\n"
            "📋 **Đề xuất:**\n"
            "1. Ghi nhận cảm xúc tốt\n"
            "2. Gợi ý thêm sản phẩm cùng danh mục hoặc combo\n\n"
            "🛍️ **Sản phẩm gợi ý thêm:**"
        )
        recommended = in_stock[:6]
    
    else:
        answer = (
            "🤖 **AI Tư vấn sản phẩm** (powered by Graph Knowledge Base + FAISS Vector Search)\n\n"
        )
        if user_id:
            behavior = GraphKnowledgeBase.get_instance().get_behavior_summary(user_id)
            answer += f"📊 **Hồ sơ của bạn:** {behavior}\n\n"
        
        if in_stock:
            answer += "🛍️ **Sản phẩm phù hợp nhất** (dựa trên phân tích ngữ nghĩa):"
        else:
            answer += "Hãy mô tả rõ hơn bạn đang tìm sản phẩm gì để tôi tư vấn chính xác hơn."
        recommended = in_stock[:6]
    
    # Build recommended_products list for UI
    recommended_products = []
    for item in (recommended if 'recommended' in dir() else in_stock[:6]):
        p = item['product']
        recommended_products.append({
            'id': p.get('id'),
            'title': p.get('name', ''),
            'name': p.get('name', ''),
            'category_name': p.get('category_name', ''),
            'brand_name': p.get('brand_name', ''),
            'price': float(p.get('price', 0)),
            'stock': int(p.get('stock', 0)),
            'image_url': p.get('image_url', ''),
            'attributes': p.get('attributes', {}),
            'relevance_score': round(item.get('score', 0), 2),
            'retrieval_source': item.get('source', 'unknown'),
        })
    
    return {
        'answer': answer,
        'recommended_products': recommended_products,
        'context_used': context[:500] if context else '',
    }


def _build_rag_answer(question, customer_id=None):
    """Main RAG entry point — called from API proxy for /reviews/rag/chat/"""
    graph, vector_store = _ensure_ai_initialized()
    
    # Log the search interaction
    if customer_id:
        graph.log_interaction(customer_id, None, 'search', query_text=question)
    
    # RAG Pipeline
    retrieved = _rag_retrieve(question, customer_id, graph, vector_store)
    context = _rag_build_context(question, customer_id, retrieved, graph)
    result = _rag_generate(question, context, retrieved, customer_id)
    
    # Map to legacy format for compatibility
    return {
        "answer": result.get("answer", ""),
        "recommended_books": result.get("recommended_products", []),
        "context": result.get("context_used", ""),
        "retrieval_count": len(retrieved),
    }


# ── INTERACTION TRACKING API ─────────────────────────────────────────────────

@csrf_exempt
def track_interaction(request):
    """Track user behavior for Graph Knowledge Base.
    POST /api/track/ {user_id, product_id, event_type, query}
    """
    if request.method != 'POST':
        return JsonResponse({"error": "POST only"}, status=405)
    
    try:
        body = json.loads(request.body or b'{}')
    except Exception:
        body = {}
    
    user_id = body.get('user_id')
    product_id = body.get('product_id')
    event_type = body.get('event_type', 'view')
    query_text = body.get('query', '')
    
    if not user_id:
        return JsonResponse({"error": "user_id required"}, status=400)
    
    graph = GraphKnowledgeBase.get_instance()
    graph.log_interaction(user_id, product_id, event_type, query_text)
    
    return JsonResponse({"status": "ok", "graph_nodes": len(graph.product_info)})


@csrf_exempt
def ai_recommend(request, customer_id):
    """AI recommendation endpoint using Graph + Vector Store.
    GET /api/ai/recommend/<customer_id>/
    """
    graph, vector_store = _ensure_ai_initialized()
    
    # 1. Graph-based recommendations (behavior)
    graph_recs = graph.get_user_top_products(customer_id, 5)
    
    # 2. Collaborative filtering
    collab_recs = graph.get_collaborative_recommendations(customer_id, 5)
    
    # 3. Category-based (preferred categories)
    pref_cats = graph.get_user_preferred_categories(customer_id)
    
    # Merge results
    seen = set()
    results = []
    
    for pid, score in graph_recs:
        if pid not in seen:
            info = graph.product_info.get(pid, {})
            if info.get('stock', 0) > 0:
                results.append({
                    'product_id': pid,
                    'name': info.get('name', ''),
                    'category': info.get('category_name', ''),
                    'price': float(info.get('price', 0)),
                    'score': round(score, 2),
                    'source': 'behavior_graph',
                })
                seen.add(pid)
    
    for pid, score in collab_recs:
        if pid not in seen:
            info = graph.product_info.get(pid, {})
            if info.get('stock', 0) > 0:
                results.append({
                    'product_id': pid,
                    'name': info.get('name', ''),
                    'category': info.get('category_name', ''),
                    'price': float(info.get('price', 0)),
                    'score': round(score, 2),
                    'source': 'collaborative_filtering',
                })
                seen.add(pid)
    
    return JsonResponse(results[:10], safe=False)




# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────

def dashboard(request):
    return render(request, "dashboard.html")


# ──────────────────────────────────────────────
# Page views (render templates, data loaded via JS)
# ──────────────────────────────────────────────

def book_list(request):
    return render(request, "products.html")


def product_list(request):
    return render(request, "products.html")


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


def clothes_list(request):
    return render(request, "clothes.html")


def account_list(request):
    return render(request, "accounts.html")


# ──────────────────────────────────────────────
# Customer-facing Store Views
# ──────────────────────────────────────────────

def store_home(request):
    return render(request, "store/store_home.html")

def store_products(request):
    return render(request, "store/store_products.html")


def store_product_detail(request, product_id):
    return render(request, "store/store_product_detail.html", {"product_id": product_id})

def store_cart(request):
    return render(request, "store/store_cart.html")

def store_orders(request):
    return render(request, "store/store_orders.html")

def store_reviews(request):
    return render(request, "store/store_reviews.html")


def store_payment_confirm(request):
    return render(request, "store/store_payment_confirm.html")

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
    """Generic proxy: /api/proxy/books/1/ → product-service:8000/books/1/"""
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
        "product": PRODUCT_SERVICE_URL,
        "cart": CART_SERVICE_URL,
        "order": ORDER_SERVICE_URL,
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
