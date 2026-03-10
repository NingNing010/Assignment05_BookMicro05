# BÁO CÁO KỸ THUẬT
# HỆ THỐNG BOOKSTORE MICROSERVICES

---

**Môn học:** Kiến trúc phần mềm  
**Giảng viên:** Thầy Trần Đình Quế  
**Sinh viên:** Lê Đăng Ninh  
**Bài tập:** Assignment 05 — BookStore Microservice Implementation  
**Repository:** https://github.com/NingNing010/Assignment05_BookMicro05  
**Ngày:** 10/03/2026  

---

## MỤC LỤC

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Công nghệ sử dụng](#3-công-nghệ-sử-dụng)
4. [Chi tiết từng Microservice](#4-chi-tiết-từng-microservice)
5. [Giao tiếp giữa các Service](#5-giao-tiếp-giữa-các-service)
6. [API Gateway & Proxy Pattern](#6-api-gateway--proxy-pattern)
7. [AI Agent — Chatbot thông minh](#7-ai-agent--chatbot-thông-minh)
8. [Giao diện người dùng](#8-giao-diện-người-dùng)
9. [Database Design](#9-database-design)
10. [Docker Deployment](#10-docker-deployment)
11. [Order Lifecycle & Business Logic](#11-order-lifecycle--business-logic)
12. [API Documentation tổng hợp](#12-api-documentation-tổng-hợp)
13. [Kết luận và hướng phát triển](#13-kết-luận-và-hướng-phát-triển)

---

## 1. TỔNG QUAN DỰ ÁN

### 1.1. Mục tiêu

Xây dựng hệ thống quản lý nhà sách (BookStore) theo kiến trúc **Microservices**, bao gồm 12 service độc lập, mỗi service đảm nhận một chức năng nghiệp vụ riêng biệt. Hệ thống hỗ trợ đầy đủ các thao tác CRUD (Create, Read, Update, Delete), quản lý đơn hàng với luồng trạng thái hoàn chỉnh, thanh toán, vận chuyển, đánh giá sách, gợi ý sách bằng AI, và một AI Agent chatbot hỗ trợ khách hàng bằng ngôn ngữ tự nhiên (tiếng Anh và tiếng Việt).

### 1.2. Phạm vi

- **12 Microservices** chạy độc lập trong Docker containers
- **API Gateway** làm điểm truy cập duy nhất (Single Entry Point)
- **2 giao diện**: Customer Storefront (khách hàng) + Admin Panel (quản trị)
- **AI Agent** xử lý ngôn ngữ tự nhiên song ngữ Anh-Việt
- **Triển khai**: Docker Compose trên máy local
- **Source control**: GitHub (main branch)

### 1.3. Danh sách 12 Microservices

| # | Service | Port | Chức năng chính |
|---|---------|------|-----------------|
| 1 | **customer-service** | 8001 | Quản lý khách hàng + AI Agent |
| 2 | **book-service** | 8002 | Quản lý sách, danh mục, nhà xuất bản |
| 3 | **cart-service** | 8003 | Quản lý giỏ hàng |
| 4 | **staff-service** | 8004 | Quản lý nhân viên + proxy quản lý sách |
| 5 | **manager-service** | 8005 | Quản lý quản lý + xem nhân viên |
| 6 | **catalog-service** | 8006 | Duyệt danh mục + sách |
| 7 | **order-service** | 8007 | Quản lý đơn hàng + trigger thanh toán/vận chuyển |
| 8 | **ship-service** | 8008 | Quản lý vận chuyển |
| 9 | **pay-service** | 8009 | Quản lý thanh toán |
| 10 | **comment-rate-service** | 8010 | Đánh giá và bình luận sách |
| 11 | **recommender-ai-service** | 8011 | Gợi ý sách bằng thuật toán AI |
| 12 | **api-gateway** | 8000 | Cổng API + giao diện web |

---

## 2. KIẾN TRÚC HỆ THỐNG

### 2.1. Tổng quan kiến trúc

Hệ thống tuân theo mô hình **Microservice Architecture** với các đặc điểm:

- **Loosely Coupled**: Mỗi service hoạt động độc lập, có database riêng
- **Single Responsibility**: Mỗi service chỉ đảm nhận một nghiệp vụ
- **API Gateway Pattern**: Mọi request từ client đều đi qua API Gateway
- **Service-to-Service Communication**: Các service giao tiếp qua HTTP REST API (synchronous)
- **Database per Service**: Mỗi service sở hữu SQLite database riêng biệt

### 2.2. Sơ đồ kiến trúc tổng quan

```
                        ┌─────────────────────┐
                        │   Client (Browser)   │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   API Gateway :8000  │
                        │  ┌─ Store (Customer) │
                        │  ├─ Admin Panel      │
                        │  ├─ API Proxy        │
                        │  └─ Agent Proxy      │
                        └──────────┬──────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
        ┌─────▼─────┐    ┌───────▼───────┐    ┌───────▼───────┐
        │ customer   │    │  book-service │    │ cart-service  │
        │ service    │    │    :8002      │    │    :8003      │
        │  :8001     │    └──────┬────────┘    └───────────────┘
        └────────────┘           │
                          ┌──────┼──────┐
                    ┌─────▼──┐ ┌─▼────┐ ┌▼──────────┐
                    │catalog │ │staff │ │comment-rate│
                    │:8006   │ │:8004 │ │:8010       │
                    └────────┘ └──┬───┘ └──────┬─────┘
                              ┌───▼───┐   ┌────▼──────────┐
                              │manager│   │recommender-ai │
                              │:8005  │   │:8011          │
                              └───────┘   └───────────────┘
        ┌──────────────────────────────────────────────────┐
        │              order-service :8007                  │
        │         ┌──────────┬──────────┐                  │
        │    ┌────▼───┐ ┌────▼───┐ ┌────▼────────┐        │
        │    │  cart   │ │  pay   │ │   ship      │        │
        │    │ :8003   │ │ :8009  │ │   :8008     │        │
        │    └─────────┘ └────────┘ └─────────────┘        │
        └──────────────────────────────────────────────────┘
```

### 2.3. Kiến trúc từng service (3-Layer)

Mỗi microservice tuân theo kiến trúc phân lớp tiêu chuẩn:

```
┌─────────────────────────────┐
│    <<service>> Tên - Port   │
│ ┌─────────────────────────┐ │
│ │   <<component>>         │ │
│ │   API Layer (views.py)  │ │
│ │   - APIView classes     │ │
│ │   - HTTP method handlers│ │
│ └───────────┬─────────────┘ │
│             │ uses           │
│ ┌───────────▼─────────────┐ │
│ │   <<component>>         │ │
│ │   Serialization Layer   │ │
│ │   - ModelSerializers    │ │
│ │   - Validation logic    │ │
│ └───────────┬─────────────┘ │
│             │ uses           │
│ ┌───────────▼─────────────┐ │
│ │   <<component>>         │ │
│ │   Data Layer (models.py)│ │
│ │   - Django ORM Models   │ │
│ └───────────┬─────────────┘ │
└─────────────┼───────────────┘
              │ persists
    ┌─────────▼──────────┐
    │  <<database>>      │
    │  SQLite (db.sqlite3)│
    └────────────────────┘
```

---

## 3. CÔNG NGHỆ SỬ DỤNG

### 3.1. Backend

| Công nghệ | Phiên bản | Vai trò |
|------------|-----------|---------|
| **Python** | 3.11 | Ngôn ngữ lập trình chính |
| **Django** | 5.x | Web framework |
| **Django REST Framework** | 3.x | RESTful API framework |
| **Requests** | latest | HTTP client cho inter-service communication |
| **SQLite** | built-in | Database cho mỗi service |

### 3.2. Frontend

| Công nghệ | Vai trò |
|------------|---------|
| **Django Templates** | Server-side rendering (HTML templates) |
| **Vanilla JavaScript** | Client-side logic, AJAX calls |
| **CSS3** | Custom design system (CSS custom properties) |
| **Google Fonts (Inter)** | Typography |
| **LocalStorage** | Session management cho customer storefront |

### 3.3. Infrastructure

| Công nghệ | Vai trò |
|------------|---------|
| **Docker** | Container runtime (v29.2.1) |
| **Docker Compose** | Multi-container orchestration |
| **Docker Desktop** | v4.63.0 (Windows) |
| **Python 3.11-slim** | Base Docker image |
| **Git / GitHub** | Version control + remote repository |

---

## 4. CHI TIẾT TỪNG MICROSERVICE

### 4.1. Customer Service (Port 8001)

**Chức năng**: Quản lý khách hàng và tích hợp AI Agent chatbot.

**Models:**
- `Customer` — `name`, `full_name`, `email` (unique), `phone`, `address`
- `AgentConversation` — `customer` (FK), `created_at`
- `AgentMessage` — `conversation` (FK), `role` (user/agent), `content`, `intent`, `created_at`

**API Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/customers/` | Lấy danh sách khách hàng |
| POST | `/customers/` | Tạo khách hàng (auto-create cart) |
| GET | `/customers/<id>/` | Lấy chi tiết 1 khách hàng |
| PUT | `/customers/<id>/` | Cập nhật toàn bộ |
| PATCH | `/customers/<id>/` | Cập nhật một phần |
| DELETE | `/customers/<id>/` | Xóa khách hàng |
| POST | `/agent/chat/` | Gửi tin nhắn tới AI Agent |
| GET | `/agent/conversations/` | Lấy lịch sử hội thoại |
| GET | `/agent/conversations/<id>/` | Chi tiết 1 hội thoại |
| GET | `/agent/help/` | Lấy danh sách lệnh agent |

**Đặc biệt:** Khi tạo customer mới, service tự động gọi `cart-service POST /carts/` để tạo giỏ hàng.

---

### 4.2. Book Service (Port 8002)

**Chức năng**: Quản lý sách, danh mục (Category), nhà xuất bản (Publisher).

**Models:**
- `Publisher` — `name`, `address`, `email`
- `Category` — `name`, `description`
- `Book` — `title`, `author`, `price`, `stock`, `description`, `isbn`, `category` (FK), `publisher` (FK)

**API Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET/POST | `/books/` | Danh sách / Tạo sách |
| GET/PUT/PATCH/DELETE | `/books/<id>/` | CRUD 1 sách |
| GET/POST | `/categories/` | Danh sách / Tạo danh mục |
| GET/PUT/PATCH/DELETE | `/categories/<id>/` | CRUD 1 danh mục |
| GET/POST | `/publishers/` | Danh sách / Tạo NXB |
| GET/PUT/PATCH/DELETE | `/publishers/<id>/` | CRUD 1 NXB |

**Serializer đặc biệt:** `BookSerializer` bổ sung 2 field read-only: `category_name` và `publisher_name` (lấy từ FK relations).

---

### 4.3. Cart Service (Port 8003)

**Chức năng**: Quản lý giỏ hàng khách hàng.

**Models:**
- `Cart` — `customer_id`
- `CartItem` — `cart` (FK), `book_id`, `quantity`

**API Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/carts/` | Tạo giỏ hàng |
| POST | `/cart-items/` | Thêm sản phẩm (auto-create cart) |
| GET | `/carts/<customer_id>/` | Xem giỏ hàng |
| DELETE | `/carts/<customer_id>/` | Xóa hết giỏ hàng |
| PATCH | `/cart-items/<id>/` | Cập nhật số lượng |
| DELETE | `/cart-items/<id>/` | Xóa 1 item |

**Logic đặc biệt:**
- `AddCartItem`: Nhận `customer_id` → tự động tạo Cart nếu chưa có (`get_or_create`)
- Nếu `book_id` đã có trong giỏ → tăng `quantity` thay vì tạo mới
- Validate sách tồn tại qua `book-service` (nếu book-service down → vẫn cho thêm)

---

### 4.4. Staff Service (Port 8004)

**Chức năng**: Quản lý nhân viên, cho phép nhân viên CRUD sách thông qua proxy.

**Models:**
- `Staff` — `name`, `email` (unique), `role` (default: "staff")

**API Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET/POST | `/staff/` | Danh sách / Tạo nhân viên |
| GET/PUT/PATCH/DELETE | `/staff/<id>/` | CRUD 1 nhân viên |
| GET | `/staff/books/` | Xem sách (proxy → book-service) |
| POST | `/staff/books/` | Tạo sách (proxy → book-service) |
| PUT/PATCH | `/staff/books/` | Sửa sách (cần `book_id` trong body) |
| DELETE | `/staff/books/?book_id=<id>` | Xóa sách (query param) |

---

### 4.5. Manager Service (Port 8005)

**Chức năng**: Quản lý quản lý viên, xem nhân viên thông qua proxy.

**Models:**
- `Manager` — `name`, `email` (unique), `department` (default: "general")

**API Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET/POST | `/managers/` | Danh sách / Tạo quản lý |
| GET/PUT/PATCH/DELETE | `/managers/<id>/` | CRUD 1 quản lý |
| GET | `/managers/staff/` | Xem nhân viên (proxy → staff-service) |

---

### 4.6. Catalog Service (Port 8006)

**Chức năng**: Duyệt danh mục sản phẩm, xem sách qua catalog.

**Models:**
- `Category` — `name`, `description`

**API Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET/POST | `/categories/` | Danh sách / Tạo danh mục |
| GET/PUT/PATCH/DELETE | `/categories/<id>/` | CRUD 1 danh mục |
| GET | `/catalog/books/` | Xem sách (proxy → book-service) |

---

### 4.7. Order Service (Port 8007)

**Chức năng**: Quản lý đơn hàng, tự động trigger thanh toán và vận chuyển.

**Models:**
- `Order` — `customer_id`, `status` (pending/confirmed/shipped/delivered/cancelled), `total_amount`, `payment_method`, `shipping_method`, `created_at`
- `OrderItem` — `order` (FK), `book_id`, `quantity`, `price`

**API Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/orders/` | Danh sách đơn hàng (kèm nested items) |
| POST | `/orders/` | Tạo đơn hàng từ giỏ hàng |
| GET | `/orders/<id>/` | Chi tiết 1 đơn hàng |
| PATCH | `/orders/<id>/` | Cập nhật trạng thái (có validation) |
| DELETE | `/orders/<id>/` | Hủy đơn hàng |

**Luồng tạo đơn hàng (POST):**
1. Lấy cart items từ `cart-service GET /carts/<customer_id>/`
2. Tạo Order với status `"pending"`
3. Tạo OrderItem cho mỗi cart item, tính `total_amount`
4. POST tới `pay-service /payments/` — tạo record thanh toán
5. POST tới `ship-service /shipments/` — tạo record vận chuyển
6. Lỗi external call → bỏ qua (fault tolerance)

**Status Transition Validation (PATCH):**

| Trạng thái hiện tại | Cho phép chuyển sang |
|---------------------|---------------------|
| `pending` | `confirmed`, `cancelled` |
| `confirmed` | `shipped`, `cancelled` |
| `shipped` | `delivered` |
| `delivered` | *(không cho chuyển)* |
| `cancelled` | *(không cho chuyển)* |

---

### 4.8. Ship Service (Port 8008)

**Chức năng**: Quản lý vận chuyển.

**Models:**
- `Shipment` — `order_id`, `customer_id`, `method` (default: "standard"), `status` (pending/processing/shipped/delivered), `tracking_number`, `created_at`

**API Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET/POST | `/shipments/` | Danh sách / Tạo shipment |
| GET/PUT/DELETE | `/shipments/<id>/` | Xem / Sửa / Xóa |

---

### 4.9. Pay Service (Port 8009)

**Chức năng**: Quản lý thanh toán.

**Models:**
- `Payment` — `order_id`, `amount`, `method` (credit_card/debit_card/paypal/bank_transfer), `status` (pending/completed/failed/refunded), `created_at`

**API Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET/POST | `/payments/` | Danh sách / Tạo payment |
| GET/PUT/DELETE | `/payments/<id>/` | Xem / Sửa / Xóa |

---

### 4.10. Comment-Rate Service (Port 8010)

**Chức năng**: Đánh giá và bình luận sách.

**Models:**
- `Review` — `book_id`, `customer_id`, `rating` (1-5), `comment`, `created_at`

**API Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET/POST | `/reviews/` | Danh sách / Tạo đánh giá |
| GET/PUT/PATCH/DELETE | `/reviews/<id>/` | CRUD 1 đánh giá |
| GET | `/reviews/book/<book_id>/` | Đánh giá theo sách |

**Logic:** Khi tạo review, validate sách tồn tại qua `book-service`.

---

### 4.11. Recommender AI Service (Port 8011)

**Chức năng**: Gợi ý sách cho khách hàng bằng thuật toán AI.

**Models:**
- `Recommendation` — `customer_id`, `book_id`, `score` (float), `created_at`

**API Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/recommendations/` | Danh sách tất cả recommendations |
| GET | `/recommendations/<customer_id>/` | Top 5 gợi ý cho khách hàng |

**Thuật toán gợi ý:**
1. Lấy tất cả sách từ `book-service`
2. Lấy tất cả reviews từ `comment-rate-service`
3. Lọc sách mà khách hàng **chưa đánh giá**
4. Tính điểm = `average_rating + random_jitter(0, 1)` (thêm yếu tố ngẫu nhiên để đa dạng kết quả)
5. Sắp xếp theo score giảm dần, trả về **Top 5**

---

### 4.12. API Gateway (Port 8000)

**Chức năng**: Cổng API duy nhất cho toàn bộ hệ thống, phục vụ giao diện web.

**Kiến trúc:**
- **Generic API Proxy** — Forward request tới microservice tương ứng
- **Customer Storefront** — 8 trang giao diện khách hàng
- **Admin Panel** — 13 trang quản trị
- **Agent Proxy** — Forward request tới AI Agent

Chi tiết xem phần 6 và phần 8.

---

## 5. GIAO TIẾP GIỮA CÁC SERVICE

### 5.1. Communication Pattern

Hệ thống sử dụng **Synchronous HTTP REST** cho mọi giao tiếp inter-service. Mỗi service gọi service khác thông qua Docker internal network (DNS: `<service-name>:8000`).

### 5.2. Service Dependency Map

```
┌─────────────────────┐       ┌──────────────────────┐
│  customer-service    │──────▶│  cart-service         │
│  (tạo customer →     │       │  (tạo cart tự động)   │
│   auto-create cart)  │       └──────────┬────────────┘
└──────────────────────┘                  │
                                          ▼
                               ┌──────────────────────┐
                               │  book-service         │
                               │  (validate sách)      │
                               └──────────┬────────────┘
                                          │
        ┌─────────────┬───────────────────┼──────────────┐
        │             │                   │              │
        ▼             ▼                   ▼              ▼
┌────────────┐ ┌────────────┐  ┌──────────────┐  ┌───────────┐
│ staff-     │ │ catalog-   │  │ comment-rate- │  │ recomm-   │
│ service    │ │ service    │  │ service       │  │ ender-ai  │
│ (CRUD sách)│ │ (xem sách) │  │(validate sách)│  │ (lấy sách │
└──────┬─────┘ └────────────┘  └───────────────┘  │  + reviews)│
       │                                           └───────────┘
       ▼
┌────────────┐
│ manager-   │
│ service    │
│ (xem staff)│
└────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    order-service                              │
│  ┌───────────┐   ┌───────────┐   ┌───────────────────┐      │
│  │cart-service│   │pay-service│   │ship-service       │      │
│  │(lấy giỏ)  │   │(tạo thanh │   │(tạo vận chuyển)   │      │
│  │           │   │ toán)     │   │                   │      │
│  └───────────┘   └───────────┘   └───────────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

### 5.3. Error Handling Strategy

Các service áp dụng **Fault Tolerance** pattern:
- **Try-Except block** bọc mọi HTTP call ra ngoài
- Nếu service đích **không phản hồi** (ConnectionError, Timeout) → xử lý graceful:
  - `cart-service`: Vẫn cho thêm sách vào giỏ nếu book-service down
  - `order-service`: Vẫn tạo order thành công nếu pay/ship service down
  - `recommender-ai-service`: Trả về kết quả rỗng nếu service phụ thuộc down
- **Timeout**: Mặc định 10 giây cho mỗi inter-service call

---

## 6. API GATEWAY & PROXY PATTERN

### 6.1. Generic API Proxy

API Gateway triển khai một **Generic Proxy** cho phép frontend gọi bất kỳ microservice nào thông qua một URL pattern duy nhất:

```
/api/proxy/<service>/<path>  →  <target_service>:8000/<service>/<path>/
```

**SERVICE_MAP — Bảng ánh xạ:**

| Service Key | Target Service URL |
|---|---|
| `books`, `publishers`, `categories` | `http://book-service:8000` |
| `customers` | `http://customer-service:8000` |
| `carts`, `cart-items` | `http://cart-service:8000` |
| `orders` | `http://order-service:8000` |
| `payments` | `http://pay-service:8000` |
| `shipments` | `http://ship-service:8000` |
| `reviews` | `http://comment-rate-service:8000` |
| `staff` | `http://staff-service:8000` |
| `managers` | `http://manager-service:8000` |
| `recommendations` | `http://recommender-ai-service:8000` |

### 6.2. Proxy Implementation

```python
@csrf_exempt
def api_proxy(request, service, path=''):
    base_url = SERVICE_MAP.get(service)
    if not base_url:
        return JsonResponse({"error": f"Unknown service: {service}"}, status=404)

    target_url = f"{base_url}/{service}/{path}"
    if not target_url.endswith('/'):
        target_url += '/'

    # Forward request với cùng method, body, headers
    method = request.method
    headers = {'Content-Type': 'application/json'}

    if method == 'GET':
        resp = requests.get(target_url, timeout=10)
    elif method == 'POST':
        resp = requests.post(target_url, data=request.body, headers=headers, timeout=10)
    elif method == 'PATCH':
        resp = requests.patch(target_url, data=request.body, headers=headers, timeout=10)
    # ... (PUT, DELETE tương tự)

    return JsonResponse(resp.json(), status=resp.status_code, safe=False)
```

### 6.3. Error Responses

| HTTP Status | Ý nghĩa |
|-------------|---------|
| `404` | Service key không tồn tại trong SERVICE_MAP |
| `405` | HTTP method không hỗ trợ |
| `503` | Không kết nối được tới service (ConnectionError) |
| `504` | Timeout khi kết nối tới service |
| `500` | Lỗi khác |

---

## 7. AI AGENT — CHATBOT THÔNG MINH

### 7.1. Tổng quan

AI Agent là chatbot tích hợp trong `customer-service`, cho phép khách hàng thực hiện các thao tác trên hệ thống bằng **ngôn ngữ tự nhiên** (hỗ trợ cả tiếng Anh và tiếng Việt).

### 7.2. Kiến trúc Agent

```
┌─────────────────────────────────────────────────┐
│                  BookStoreAgent                  │
│                                                  │
│  ┌───────────────┐    ┌───────────────────────┐ │
│  │ Intent Parser  │    │  Tool Functions       │ │
│  │ (regex-based)  │───▶│  (HTTP wrappers)      │ │
│  │                │    │                       │ │
│  │ 14 intents     │    │ tool_search_books()   │ │
│  │ 28 patterns    │    │ tool_view_cart()      │ │
│  │ EN + VN        │    │ tool_add_to_cart()    │ │
│  │ + diacritics   │    │ tool_place_order()    │ │
│  │   normalization│    │ tool_rate_book()      │ │
│  └───────────────┘    │ tool_get_reviews()    │ │
│                        │ tool_cancel_order()   │ │
│                        │ ... (13 tools total)  │ │
│                        └──────────┬────────────┘ │
└───────────────────────────────────┼──────────────┘
                                    │ HTTP calls
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
              book-service   cart-service    order-service
              comment-rate   recommender-ai
```

### 7.3. Intent Parser

Agent sử dụng **Regex-based Intent Parsing** với 28 regex patterns (14 cặp Anh-Việt):

| Intent | Ví dụ tiếng Anh | Ví dụ tiếng Việt |
|--------|------------------|-------------------|
| `search_books` | "search books about Python" | "tìm sách Python" |
| `view_book` | "book #1" | "chi tiết sách #1" |
| `update_book_price` | "update book #1 price to 29.99" | "cập nhật sách #1 giá 29.99" |
| `add_to_cart` | "add book #3 to cart" | "thêm sách #3 vào giỏ" |
| `view_cart` | "view my cart" | "xem giỏ hàng" |
| `remove_cart_item` | "remove item #1 from cart" | "xóa item #1 khỏi giỏ" |
| `clear_cart` | "clear cart" | "xóa hết giỏ hàng" |
| `place_order` | "place order" | "đặt hàng" |
| `cancel_order` | "cancel order #1" | "hủy đơn #1" |
| `view_orders` | "view my orders" | "xem đơn hàng" |
| `rate_book` | "rate book #2 5 stars Great!" | "đánh giá sách #2 5 sao" |
| `get_reviews` | "reviews for book #1" | "đánh giá sách #1" |
| `get_recommendations` | "recommend" | "gợi ý sách" |
| `help` | "help" | "giúp" |

### 7.4. Diacritics Normalization

Để hỗ trợ người dùng gõ tiếng Việt **không dấu**, Agent có hàm `_remove_diacritics()`:

```python
def _remove_diacritics(text):
    nfkd = unicodedata.normalize('NFD', text)
    stripped = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return stripped.replace('đ', 'd').replace('Đ', 'D')
```

Khi regex match lần 1 thất bại, Agent thử lại với text đã bỏ dấu:
- "tim sach Python" → match "tìm sách Python" pattern
- "dat hang" → match "đặt hàng" pattern

### 7.5. Conversation Persistence

Mỗi cuộc hội thoại được lưu trong database:
- `AgentConversation` — liên kết với Customer
- `AgentMessage` — chứa `role` (user/agent), `content`, `intent`
- Có thể tiếp tục hội thoại cũ qua `conversation_id`

### 7.6. Tool Functions

Agent sử dụng 13 tool functions, mỗi function là wrapper cho 1 HTTP call:

| Tool | Target Service | Mô tả |
|------|---|---|
| `tool_search_books(query)` | book-service | Tìm kiếm/lọc sách |
| `tool_view_book(book_id)` | book-service | Xem chi tiết sách |
| `tool_update_book_price(book_id, price)` | book-service | Cập nhật giá sách |
| `tool_view_cart(customer_id)` | cart-service | Xem giỏ hàng |
| `tool_add_to_cart(customer_id, book_id, qty)` | cart-service | Thêm vào giỏ |
| `tool_remove_cart_item(item_id)` | cart-service | Xóa item khỏi giỏ |
| `tool_clear_cart(customer_id)` | cart-service | Xóa hết giỏ |
| `tool_place_order(customer_id, pay, ship)` | order-service | Đặt hàng |
| `tool_cancel_order(order_id)` | order-service | Hủy đơn |
| `tool_view_orders(customer_id)` | order-service | Xem đơn hàng |
| `tool_rate_book(customer_id, book_id, rating, comment)` | comment-rate-service | Đánh giá sách |
| `tool_get_reviews(book_id)` | comment-rate-service | Xem đánh giá |
| `tool_get_recommendations(customer_id)` | recommender-ai-service | Gợi ý sách |

Mỗi tool sử dụng `safe_request()` wrapper với error handling cho ConnectionError, Timeout, HTTPError.

---

## 8. GIAO DIỆN NGƯỜI DÙNG

### 8.1. Kiến trúc giao diện

Hệ thống có **2 giao diện** riêng biệt, cùng phục vụ từ API Gateway:

| Giao diện | URL Prefix | Theme | Đối tượng |
|-----------|-----------|-------|-----------|
| **Customer Storefront** | `/` và `/store/` | Light (trắng, xanh) | Khách hàng |
| **Admin Panel** | `/admin-panel/` | Dark (navy, accent) | Quản trị viên |

### 8.2. Customer Storefront

**8 trang giao diện:**

| Trang | URL | Mô tả |
|-------|-----|-------|
| Trang chủ | `/` | Hero section, tìm kiếm, danh sách sách |
| Danh sách sách | `/store/books/` | Lọc theo danh mục, sắp xếp |
| Chi tiết sách | `/store/book/<id>/` | Ảnh bìa, thông tin, đánh giá, thêm giỏ |
| Giỏ hàng | `/store/cart/` | Danh sách items, +/- số lượng, thanh toán |
| Đơn hàng | `/store/orders/` | Lịch sử đơn, hủy/xác nhận nhận hàng |
| Đăng nhập | `/store/login/` | Đăng nhập bằng email |
| Đăng ký | `/store/register/` | Tạo tài khoản mới |
| AI Chat | `/admin-panel/agent/` | Chat với AI Agent |

**Design System:**
- Font: Inter (Google Fonts)
- CSS Custom Properties: `--navy`, `--gold`, `--accent`, `--light`, responsive
- Components: `.book-card`, `.btn` variants, `.tag` badges, `.toast`, `.alert-banner`
- Gradient book covers với emoji icons
- Responsive grid layout

**Authentication:**
- Sử dụng `localStorage` để lưu customer session
- Login bằng email lookup (tìm customer theo email)
- Register tạo customer mới qua API
- `getCustomer()` / `setCustomer()` / `logout()` JS functions

### 8.3. Admin Panel

**13 trang quản trị:**

| Trang | URL | Chức năng |
|-------|-----|-----------|
| Dashboard | `/admin-panel/` | Tổng quan, thống kê, quick actions |
| Books | `/admin-panel/books/` | CRUD sách (modal form) |
| Categories | `/admin-panel/categories/` | CRUD danh mục |
| Publishers | `/admin-panel/publishers/` | CRUD nhà xuất bản |
| Customers | `/admin-panel/customers/` | CRUD khách hàng |
| Orders | `/admin-panel/orders/` | Quản lý đơn hàng (xác nhận/giao/nhận/hủy) |
| Payments | `/admin-panel/payments/` | Xem/quản lý thanh toán |
| Shipments | `/admin-panel/shipments/` | Xem/quản lý vận chuyển |
| Reviews | `/admin-panel/reviews/` | Quản lý đánh giá |
| Staff | `/admin-panel/staff/` | CRUD nhân viên |
| Managers | `/admin-panel/managers/` | CRUD quản lý |
| AI Agent | `/admin-panel/agent/` | Chat với AI Agent |
| Recommendations | `/admin-panel/recommendations/<id>/` | Xem gợi ý cho KH |

**Design System:**
- Dark theme (navy background, light text)
- Sidebar navigation with sections (Main, Catalog, Customers, Operations)
- Topbar with page title
- CSS: `.card`, `.stat-card`, `.table`, `.tag`, `.btn` variants, `.modal`
- All pages use JavaScript + `fetch()` to call `/api/proxy/` endpoints
- `apiCall()` helper function for JSON CRUD operations

---

## 9. DATABASE DESIGN

### 9.1. Database per Service Pattern

Mỗi microservice có **SQLite database riêng** (`db.sqlite3`), đảm bảo:
- **Data isolation**: Không service nào truy cập trực tiếp database của service khác
- **Independent deployment**: Mỗi service có thể migrate schema độc lập
- **Loose coupling**: Thay đổi schema 1 service không ảnh hưởng service khác

### 9.2. Entity Relationship Diagrams

**Book Service:**
```
Publisher(id, name, address, email)
    │
    │ 1:N (nullable)
    ▼
Book(id, title, author, price, stock, description, isbn, category_id, publisher_id)
    ▲
    │ 1:N (nullable)
    │
Category(id, name, description)
```

**Customer Service:**
```
Customer(id, name, full_name, email, phone, address)
    │
    │ 1:N
    ▼
AgentConversation(id, customer_id, created_at)
    │
    │ 1:N
    ▼
AgentMessage(id, conversation_id, role, content, intent, created_at)
```

**Cart Service:**
```
Cart(id, customer_id)
    │
    │ 1:N
    ▼
CartItem(id, cart_id, book_id, quantity)
```

**Order Service:**
```
Order(id, customer_id, status, total_amount, payment_method, shipping_method, created_at)
    │
    │ 1:N
    ▼
OrderItem(id, order_id, book_id, quantity, price)
```

### 9.3. Cross-Service References

Do mỗi service có database riêng, các quan hệ cross-service được thực hiện qua **ID references** (không phải FK constraints):

| Service | Field | Tham chiếu tới |
|---------|-------|----------------|
| Cart | `customer_id` | customer-service → Customer.id |
| CartItem | `book_id` | book-service → Book.id |
| Order | `customer_id` | customer-service → Customer.id |
| OrderItem | `book_id` | book-service → Book.id |
| Shipment | `order_id`, `customer_id` | order-service, customer-service |
| Payment | `order_id` | order-service → Order.id |
| Review | `book_id`, `customer_id` | book-service, customer-service |
| Recommendation | `customer_id`, `book_id` | customer-service, book-service |

---

## 10. DOCKER DEPLOYMENT

### 10.1. Dockerfile (Template chung)

Tất cả 12 services sử dụng Dockerfile cùng cấu trúc:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py makemigrations app && python manage.py migrate

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

**Đặc điểm:**
- Base image: `python:3.11-slim` (nhẹ, production-ready)
- Database migration chạy tại build time
- Serve qua Django development server (port 8000)
- Mỗi container expose port 8000 nội bộ

### 10.2. Docker Compose

```yaml
services:
  book-service:
    build: ./book-service
    ports: ["8002:8000"]

  cart-service:
    build: ./cart-service
    ports: ["8003:8000"]
    depends_on: [book-service]

  customer-service:
    build: ./customer-service
    ports: ["8001:8000"]
    depends_on: [cart-service]

  order-service:
    build: ./order-service
    ports: ["8007:8000"]
    depends_on: [pay-service, ship-service, cart-service]

  api-gateway:
    build: ./api-gateway
    ports: ["8000:8000"]
    depends_on: [tất cả 11 services]
```

### 10.3. Service Dependencies (Boot Order)

```
Layer 1 (no dependencies):
  book-service, pay-service, ship-service

Layer 2 (depends on Layer 1):
  cart-service → book-service
  catalog-service → book-service
  staff-service → book-service
  comment-rate-service → book-service

Layer 3 (depends on Layer 1+2):
  customer-service → cart-service
  manager-service → staff-service
  order-service → pay-service, ship-service, cart-service
  recommender-ai-service → book-service, comment-rate-service

Layer 4 (depends on all):
  api-gateway → all 11 services
```

### 10.4. Network

Docker Compose tự động tạo một **bridge network** chung. Các service giao tiếp qua DNS name:
- `http://book-service:8000`
- `http://cart-service:8000`
- `http://customer-service:8000`
- ... (tất cả đều port 8000 nội bộ)

### 10.5. Port Mapping

| Container (internal) | Host (external) |
|---------------------|-----------------|
| api-gateway:8000 | localhost:8000 |
| customer-service:8000 | localhost:8001 |
| book-service:8000 | localhost:8002 |
| cart-service:8000 | localhost:8003 |
| staff-service:8000 | localhost:8004 |
| manager-service:8000 | localhost:8005 |
| catalog-service:8000 | localhost:8006 |
| order-service:8000 | localhost:8007 |
| ship-service:8000 | localhost:8008 |
| pay-service:8000 | localhost:8009 |
| comment-rate-service:8000 | localhost:8010 |
| recommender-ai-service:8000 | localhost:8011 |

---

## 11. ORDER LIFECYCLE & BUSINESS LOGIC

### 11.1. Order Flow Sequence

```
Customer (Browser)                API Gateway              order-service        cart-service      pay-service     ship-service
    │                                │                         │                    │                 │               │
    │  Click "Thanh toán"            │                         │                    │                 │               │
    │───POST /api/proxy/orders/─────▶│                         │                    │                 │               │
    │  {customer_id: 1}              │──POST /orders/─────────▶│                    │                 │               │
    │                                │                         │──GET /carts/1/────▶│                 │               │
    │                                │                         │◀───cart items──────│                 │               │
    │                                │                         │                    │                 │               │
    │                                │                         │  Create Order       │                 │               │
    │                                │                         │  (status=pending)   │                 │               │
    │                                │                         │  Create OrderItems  │                 │               │
    │                                │                         │  Calculate total    │                 │               │
    │                                │                         │                    │                 │               │
    │                                │                         │──POST /payments/──────────────────▶│               │
    │                                │                         │                    │                 │               │
    │                                │                         │──POST /shipments/──────────────────────────────────▶│
    │                                │                         │                    │                 │               │
    │                                │◀──201 Order created─────│                    │                 │               │
    │◀──Order response───────────────│                         │                    │                 │               │
```

### 11.2. Status Transition Diagram

```
                    ┌──────────┐
                    │ PENDING  │
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              ▼                     ▼
        ┌───────────┐        ┌───────────┐
        │ CONFIRMED │        │ CANCELLED │
        └─────┬─────┘        └───────────┘
              │                     ▲
              ▼                     │
        ┌───────────┐               │
        │  SHIPPED  │───────────────┘
        └─────┬─────┘    (chỉ pending/confirmed
              │           mới hủy được)
              ▼
        ┌───────────┐
        │ DELIVERED │
        └───────────┘
```

### 11.3. Actions theo Role

| Trạng thái | Admin Panel | Khách hàng |
|-----------|-------------|------------|
| `pending` | ✅ Xác nhận / ❌ Hủy | ❌ Hủy đơn |
| `confirmed` | 🚚 Giao hàng / ❌ Hủy | — (chờ giao) |
| `shipped` | 📬 Đã nhận | 📬 Đã nhận hàng |
| `delivered` | — | — |
| `cancelled` | — | — |

---

## 12. API DOCUMENTATION TỔNG HỢP

### 12.1. Tổng số Endpoints

| Service | Endpoints | Methods |
|---------|-----------|---------|
| customer-service | 10 | GET, POST, PUT, PATCH, DELETE |
| book-service | 12 | GET, POST, PUT, PATCH, DELETE |
| cart-service | 6 | GET, POST, PATCH, DELETE |
| staff-service | 8 | GET, POST, PUT, PATCH, DELETE |
| manager-service | 5 | GET, POST, PUT, PATCH, DELETE |
| catalog-service | 7 | GET, POST, PUT, PATCH, DELETE |
| order-service | 5 | GET, POST, PATCH, DELETE |
| ship-service | 4 | GET, POST, PUT, DELETE |
| pay-service | 4 | GET, POST, PUT, DELETE |
| comment-rate-service | 7 | GET, POST, PUT, PATCH, DELETE |
| recommender-ai-service | 2 | GET |
| api-gateway | 5 (API) + 21 (pages) | ALL |
| **Tổng** | **~96 endpoints** | |

### 12.2. Request/Response Format

- **Content-Type**: `application/json`
- **Successful responses**: `200 OK`, `201 Created`, `204 No Content`
- **Error responses**: `400 Bad Request`, `404 Not Found`, `405 Method Not Allowed`, `500/503/504` (gateway errors)
- **Error format**: `{"error": "Error message"}`

### 12.3. Authentication

- **Admin Panel**: Sử dụng Django admin auth (username/password: `admin/admin123`)
- **Customer Storefront**: LocalStorage-based session (email lookup, không password)
- **API Endpoints**: Không có authentication middleware (open access cho demo purpose)

---

## 13. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

### 13.1. Kết quả đạt được

- ✅ Triển khai thành công **12 microservices** với đầy đủ CRUD operations
- ✅ **API Gateway** với generic proxy pattern, routing tới 11 backend services
- ✅ **AI Agent** chatbot song ngữ Anh-Việt với 14 intents, 28 regex patterns
- ✅ **Docker Compose** deployment với 12 containers chạy đồng thời
- ✅ **2 giao diện web**: Customer Storefront (light theme) + Admin Panel (dark theme)
- ✅ **Order management** với status transition validation hoàn chỉnh
- ✅ **Inter-service communication** qua HTTP REST với fault tolerance
- ✅ **Recommender AI** tính toán gợi ý sách dựa trên reviews và ratings
- ✅ **Source control** trên GitHub với commit history rõ ràng

### 13.2. Nguyên tắc thiết kế đã áp dụng

| Nguyên tắc | Mô tả |
|-----------|-------|
| **Single Responsibility** | Mỗi service chỉ đảm nhận 1 nghiệp vụ |
| **Database per Service** | Mỗi service có database riêng biệt |
| **API Gateway Pattern** | Điểm truy cập duy nhất cho client |
| **Proxy Pattern** | Gateway forward request tới backend services |
| **Fault Tolerance** | Graceful handling khi service phụ thuộc down |
| **Loose Coupling** | Services giao tiếp qua HTTP API, không share database |
| **Independent Deployment** | Mỗi service build/deploy riêng trong Docker |

### 13.3. Hạn chế

- Sử dụng **SQLite** (không phù hợp production, nên dùng PostgreSQL/MySQL)
- Chưa có **authentication/authorization** đầy đủ (JWT tokens, OAuth2)
- Sử dụng **Django development server** (nên dùng Gunicorn + Nginx)
- **Synchronous communication** only (chưa có message queue như RabbitMQ/Kafka)
- Chưa có **health check endpoints** cho Docker health monitoring
- Chưa có **centralized logging** (ELK stack) và **monitoring** (Prometheus/Grafana)
- Chưa có **API rate limiting** và **circuit breaker** pattern

### 13.4. Hướng phát triển

- Chuyển sang **PostgreSQL** cho production database
- Thêm **JWT Authentication** middleware cho tất cả API endpoints
- Triển khai **message queue** (RabbitMQ) cho asynchronous events (order placed → payment + shipping)
- Thêm **Nginx** reverse proxy và **Gunicorn** WSGI server
- Cài đặt **Kubernetes** cho production orchestration
- Thêm **CI/CD pipeline** (GitHub Actions) cho automated testing và deployment
- Tích hợp **LLM** (GPT/Gemini) thay thế regex-based intent parsing cho AI Agent
- Thêm **Elasticsearch** cho full-text search sách
- Cài đặt **Redis** cho caching và session storage

---

**--- HẾT BÁO CÁO ---**
