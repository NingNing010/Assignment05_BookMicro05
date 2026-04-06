# BookStore Microservices - Comprehensive Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Microservices](#microservices)
4. [Database Models](#database-models)
5. [Features](#features)
6. [User Store Features](#user-store-features)
7. [Admin Panel Features](#admin-panel-features)
8. [AI Agent Features](#ai-agent-features)
9. [API Endpoints](#api-endpoints)
10. [Setup & Installation](#setup--installation)
11. [Running the Project](#running-the-project)
12. [Technology Stack](#technology-stack)
13. [Project Structure](#project-structure)

---

## 🎯 Project Overview

**BookStore Microservices** is a comprehensive e-commerce platform built using microservices architecture. The system allows customers to browse books, add items to cart, place orders, and write reviews. Administrators can manage inventory, monitor orders, process payments, and track shipments. The platform features an AI assistant for enhanced customer support and personalized recommendations.

### Key Highlights:
- ✅ **Microservices Architecture** with 16 independent services
- ✅ **REST APIs** for all operations
- ✅ **JWT Authentication** with role-based access control (RBAC)
- ✅ **Stock Management** with multi-layer validation
- ✅ **Payment Processing** (COD, Bank Transfer, Credit/Debit Cards)
- ✅ **Order Management** with Saga pattern
- ✅ **AI-Powered Assistant** with NLP intent recognition
- ✅ **Review System** with ratings and comments
- ✅ **Book Recommendations** engine
- ✅ **Responsive Web Interface** for customers and admins
- ✅ **Docker Compose** for easy deployment

---

## 🏗️ Architecture

### Architecture Pattern: API Gateway with Microservices

```
┌─────────────────────────────────────────────┐
│           API Gateway (Port 8000)           │
│  - Request Routing & Proxying               │
│  - Authentication & Authorization (RBAC)    │
│  - Rate Limiting                            │
│  - Template Rendering                       │
│  - Static File Serving                      │
└─────────────┬───────────────────────────────┘
              │
      ┌───────┼───────┬───────────┬──────────┬──────────┬─────────┐
      ▼       ▼       ▼           ▼          ▼          ▼         ▼
  ┌────────────────────────────────────────────────────────────────────┐
  │  Book  │ Auth   │ Cart   │ Order  │ Payment│ Shipping│ Customer   │
  │Service │Service │Service │Service │Service │Service  │Service     │
  │(8002)  │(8012)  │(8003)  │(8004)  │(8009)  │(8007)   │(8001)      │
  └────────────────────────────────────────────────────────────────────┘
      │       │        │        │        │         │          │
  ┌───┼───────┼────────┼────────┼────────┼─────────┼──────────┴──────────┬─────┐
  │   │       │        │        │        │         │                     │     │
  ▼   ▼       ▼        ▼        ▼        ▼         ▼                     ▼     ▼
┌─────────────────────────────────────────────────┐            ┌──────────────┐
│     Shared MySQL Database (Host Machine)        │            │   RabbitMQ   │
│  ┌─────────┬────────┬────────┬────────┬─────┐  │            │  Message Bus │
│  │Book_DB  │Auth_DB │Cart_DB │Order_DB│...  │  │            └──────────────┘
│  └─────────┴────────┴────────┴────────┴─────┘  │
└─────────────────────────────────────────────────┘
```

### Data Flow:
1. **Customer Request** → API Gateway
2. **Authentication Check** → Auth Service
3. **Authorization Validation** → RBAC Policy Check
4. **Rate Limiting** → Per-user/IP throttling
5. **Service Routing** → Appropriate microservice
6. **Business Logic** → Service-specific processing
7. **Data Persistence** → Microservice database
8. **Event Publishing** → RabbitMQ (optional) or SagaEvent store
9. **Response** → Back through gateway to client

---

## 🔧 Microservices

### 1. **API Gateway** (Port 8000)
**Purpose:** Central entry point for all client requests
- Template rendering for user store and admin panel
- Request proxying to backend services
- JWT token validation and RBAC enforcement
- Rate limiting (guest: 60 req/min, user: 120 req/min, admin: 300 req/min)
- Health check endpoints (/health/live/, /health/ready/)
- Static file serving

**Key Dependencies:**
- book-service (8002)
- auth-service (8012)
- cart-service (8003)
- order-service (8004)
- pay-service (8009)
- ship-service (8007)
- customer-service (8001)
- comment-rate-service
- recommendation-ai-service
- And 5+ other services

---

### 2. **Auth Service** (Port 8012)
**Purpose:** User authentication and JWT token management
- User registration and login
- JWT token generation (access + refresh tokens)
- Token validation
- Password hashing and security
- User account management

**Database:** `bookstore_auth`
- User credentials storage
- Token blacklist (logout support)

---

### 3. **Book Service** (Port 8002)
**Purpose:** Book catalog management
- List all books with filtering and sorting
- Book details retrieval
- Create/update/delete books (admin)
- Publisher management
- Category management
- Stock inventory management
- **Stock validation** (must be integer ≥ 0)
- **Price validation** (must be > 0)

**Database:** `bookstore_book`
- Book records
- Publisher information
- Category information

**Key Models:**
```python
Book:
  - title (string)
  - author (string)
  - price (decimal)
  - stock (integer, ≥ 0)
  - description (text)
  - isbn (string)
  - category (FK → Category)
  - publisher (FK → Publisher)

Publisher:
  - name (string)
  - address (text)
  - email (string)

Category:
  - name (string)
  - description (text)
```

---

### 4. **Cart Service** (Port 8003)
**Purpose:** Shopping cart management per customer
- Add item to cart (with stock validation)
- Update cart item quantity (with stock validation)
- Remove item from cart
- Get cart contents
- **Stock check** before allowing item addition/quantity increase
- **Prevents exceeding available inventory**

**Database:** `bookstore_cart`
- Cart records per customer
- Cart items with quantities

**Key Models:**
```python
Cart:
  - customer_id (integer)

CartItem:
  - cart (FK → Cart)
  - book_id (integer)
  - quantity (integer)
```

**Validation Logic:**
- When adding/updating: Check book stock via book-service
- Return 409 CONFLICT if requested quantity > available stock
- Prevent manipulation of inventory through cart

---

### 5. **Order Service** (Port 8004)
**Purpose:** Order orchestration with Saga pattern
- Create orders with full validation
- Track order status throughout lifecycle
- **Multi-layer stock validation:**
  1. Pre-creation: Validate all items have sufficient stock
  2. Return 409 CONFLICT with insufficient_items details if validation fails
  3. Post-confirm: Reduce book stock via PATCH to book-service
- Clear customer cart after successful order
- Order history retrieval
- Order status management (pending → confirmed → shipped → delivered)

**Database:** `bookstore_order`
- Order records (master)
- Order items (line items)
- Saga events (event sourcing)

**Key Models:**
```python
Order:
  - customer_id (integer)
  - status (choices: pending, payment_reserved, shipping_reserved, confirmed, compensating, shipped, delivered, cancelled)
  - total_amount (decimal)
  - payment_method (string)
  - shipping_method (string)
  - created_at (datetime)

OrderItem:
  - order (FK → Order)
  - book_id (integer)
  - quantity (integer)
  - price (decimal)

SagaEvent:
  - topic (string)
  - payload (JSON)
  - created_at (datetime)
```

**Order Flow:**
```
User requests Order Creation
    ↓
Validate cart not empty
    ↓
Validate payment_method (normalize COD/bank_transfer variants)
    ↓
✓ STOCK CHECK 1: Get current stock for each book
    ↓ (if insufficient → return 409 with details)
    ↓ (if sufficient → continue)
Create Order (status: pending)
    ↓
✓ STOCK REDUCTION: PATCH /books/{id}/ with new_stock = stock - quantity
    ↓
Update Order status: confirmed
    ↓
Reserve Payment via pay-service
    ↓
Reserve Shipping via ship-service
    ↓
✓ CLEAR CART: DELETE /carts/{customer_id}/
    ↓
Publish Order.Created event
    ↓
Return Order confirmation to user
```

---

### 6. **Payment Service** (Port 8009)
**Purpose:** Payment processing and transaction management
- Create payment records
- Update payment status
- Track payment methods
- Refund processing
- **Supported Payment Methods:**
  - COD (Cash On Delivery)
  - Bank Transfer
  - Credit Card
  - Debit Card
  - PayPal

**Database:** `bookstore_payment`
- Payment transactions
- Payment status tracking

**Key Models:**
```python
Payment:
  - order_id (integer)
  - amount (decimal)
  - method (choices: cod, credit_card, debit_card, paypal, bank_transfer)
  - status (choices: pending, reserved, completed, failed, released, refunded)
  - created_at (datetime)
```

---

### 7. **Shipping Service** (Port 8007)
**Purpose:** Shipment management and logistics
- Create shipment records
- Update shipment status
- Track deliveries
- Shipping method management

**Database:** `bookstore_shipment`

---

### 8. **Customer Service** (Port 8001)
**Purpose:** Customer profile and AI chat management
- Customer registration
- Profile management (name, email, phone, address)
- AI conversation history storage
- Agent message logging

**Database:** `bookstore_customer`

**Key Models:**
```python
Customer:
  - name (string)
  - full_name (string)
  - email (string, unique)
  - phone (string)
  - address (text)

AgentConversation:
  - customer (FK → Customer)
  - created_at (datetime)

AgentMessage:
  - conversation (FK → AgentConversation)
  - role (choices: user, agent)
  - content (text)
  - intent (string)
  - created_at (datetime)
```

---

### 9. **AI Agent (Part of Customer Service)**
**Purpose:** Natural language processing for customer support
- Intent recognition (add_to_cart, check_book_stock, top_rated_books, etc.)
- Tool-based command execution
- Conversation history management
- Contextual responses

**Supported Intents:**
- `add_to_cart`: Add book to customer's cart with quantity
- `check_book_stock`: Check availability of specific book
- `top_rated_books`: Get highest-rated books (sorted by rating)
- `list_books`: Browse available books
- `view_cart`: Show current cart contents
- `help`: Display available commands

**Tool Functions:**
- `tool_add_to_cart()` - Calls cart-service to add item
- `tool_check_book_stock()` - Queries book-service for stock
- `tool_top_rated_books()` - Fetches reviews from comment-rate-service
- And more...

---

### 10. **Comment & Rate Service** (comment-rate-service)
**Purpose:** Review and rating management
- Create reviews (rating 1-5 + comment)
- View reviews for books
- Filter reviews by customer
- Rating aggregation

**Database:** `bookstore_comment_rate`

**Key Models:**
```python
Review:
  - book_id (integer)
  - customer_id (integer)
  - rating (integer, 1-5)
  - comment (text)
  - created_at (datetime)
```

---

### 11. **Catalog Service** (Port 8006)
**Purpose:** Advanced catalog features
- Book search and filtering
- Category browsing
- Publisher listings
- Advanced product catalog management

---

### 12. **Recommendation Service** (recommender-ai-service)
**Purpose:** Personalized book recommendations
- ML-based recommendation engine
- Collaborative filtering
- Content-based recommendations
- Trending books
- Based on customer history and reviews

---

### 13. **Staff Service** (Port 8004)
**Purpose:** Staff account and role management
- Staff profile management
- Staff permissions
- Staff activity logging

---

### 14. **Manager Service** (Port 8005)
**Purpose:** Manager-level operations
- Manager account management
- Team management
- Advanced reporting
- Business analytics

---

### 15. **Clothes Service** (clothes-service)
**Purpose:** Alternative product catalog (for store expansion)
- Clothing inventory management
- Similar structure to book-service

---

### 16. **RabbitMQ** (Message Bus)
**Purpose:** Asynchronous event publishing and consumption
- Event topic exchange
- Service-to-service communication
- Order event publishing
- Optional event stream processing

---

## 📊 Database Models

### Book Service Database

```sql
CREATE TABLE book_publisher (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255),
  address TEXT,
  email VARCHAR(255)
);

CREATE TABLE book_category (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255),
  description TEXT
);

CREATE TABLE book_book (
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255),
  author VARCHAR(255),
  price DECIMAL(10, 2),
  stock INT DEFAULT 0,
  description TEXT,
  isbn VARCHAR(20),
  category_id INT,
  publisher_id INT,
  FOREIGN KEY (category_id) REFERENCES book_category(id),
  FOREIGN KEY (publisher_id) REFERENCES book_publisher(id)
);
```

### Order Service Database

```sql
CREATE TABLE order_order (
  id INT PRIMARY KEY AUTO_INCREMENT,
  customer_id INT,
  status VARCHAR(20),
  total_amount DECIMAL(10, 2),
  payment_method VARCHAR(50),
  shipping_method VARCHAR(50),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_orderitem (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT,
  book_id INT,
  quantity INT,
  price DECIMAL(10, 2),
  FOREIGN KEY (order_id) REFERENCES order_order(id)
);

CREATE TABLE order_sagaevent (
  id INT PRIMARY KEY AUTO_INCREMENT,
  topic VARCHAR(120),
  payload LONGTEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Cart Service Database

```sql
CREATE TABLE cart_cart (
  id INT PRIMARY KEY AUTO_INCREMENT,
  customer_id INT UNIQUE
);

CREATE TABLE cart_cartitem (
  id INT PRIMARY KEY AUTO_INCREMENT,
  cart_id INT,
  book_id INT,
  quantity INT,
  FOREIGN KEY (cart_id) REFERENCES cart_cart(id)
);
```

### Payment Service Database

```sql
CREATE TABLE pay_payment (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT,
  amount DECIMAL(10, 2),
  method VARCHAR(50),
  status VARCHAR(20),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Customer Service Database

```sql
CREATE TABLE customer_customer (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255),
  full_name VARCHAR(255),
  email VARCHAR(255) UNIQUE,
  phone VARCHAR(20),
  address TEXT
);

CREATE TABLE customer_agentconversation (
  id INT PRIMARY KEY AUTO_INCREMENT,
  customer_id INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customer_customer(id)
);

CREATE TABLE customer_agentmessage (
  id INT PRIMARY KEY AUTO_INCREMENT,
  conversation_id INT,
  role VARCHAR(10),
  content LONGTEXT,
  intent VARCHAR(50),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (conversation_id) REFERENCES customer_agentconversation(id)
);
```

### Review/Comment Service Database

```sql
CREATE TABLE comment_review (
  id INT PRIMARY KEY AUTO_INCREMENT,
  book_id INT,
  customer_id INT,
  rating INT,
  comment TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## ✨ Features

### Core Features
1. ✅ User Authentication (JWT-based)
2. ✅ Role-Based Access Control (RBAC)
3. ✅ Book Catalog Management
4. ✅ Shopping Cart Management
5. ✅ Order Placement & Tracking
6. ✅ Payment Processing (Multiple methods)
7. ✅ Shipment Tracking
8. ✅ Review & Rating System
9. ✅ AI-Powered Customer Support
10. ✅ Book Recommendations Engine

### Advanced Features
1. ✅ **Stock Management** (Multi-layer validation & reduction)
2. ✅ **Saga Pattern** for order orchestration
3. ✅ **Event Sourcing** via RabbitMQ
4. ✅ **Rate Limiting** per user/IP
5. ✅ **Health Checks** (liveness + readiness)
6. ✅ **Responsive UI** (Bootstrap)
7. ✅ **Admin Dashboard** with analytics
8. ✅ **Modal dialogs** for quick actions
9. ✅ **Centered authentication** layouts
10. ✅ **Real-time AI chat**

---

## 🛒 User Store Features

### 1. **Homepage** (`/store/` or `/`)
- Featured books display
- Category browsing
- Quick search/filter
- Out-of-stock prevention (buttons disabled for unavailable items)
- Add to cart functionality

### 2. **Books Catalog** (`/store/books/`)
- Browse all books
- Filter by category
- Sort by price/rating/date
- **Popup book detail modal** (not full-page navigation)
  - Shows book details: title, author, price, stock, description
  - Quick add-to-cart from modal
  - Link to full detail page
- Out-of-stock indicators

### 3. **Book Detail** (`/store/book/<id>/`)
- Full book information
- Reviews and ratings
- Detailed description
- Publisher and category info
- Quantity selector (respects max stock)
- Add to cart button

### 4. **Shopping Cart** (`/store/cart/`)
- View all cart items
- Adjust quantities (with stock validation)
- Remove items
- Cart total calculation
- **Payment method selector:**
  - COD (Cash On Delivery)
  - Bank Transfer
  - Credit/Debit Card
  - PayPal
- Place order button
- Error handling for:
  - Out-of-stock items (409 CONFLICT)
  - Empty cart
  - Invalid quantities

### 5. **Orders** (`/store/orders/`)
- View order history
- Order details (items, total, status)
- Order status tracking
- Shipment information

### 6. **Reviews Tab** (`/store/reviews/`)
- View all reviews written by user
- Create new review:
  - Select book from dropdown
  - Rate 1-5 stars
  - Write comment
  - Submit review
- Filter reviews by user
- Display average rating per book

### 7. **Authentication**
- **Login** (`/store/login/`)
  - Email and password
  - Centered layout on page
  - Error messages for invalid credentials
  - Register link
  
- **Register** (`/store/register/`)
  - Email, password, confirm password
  - Centered layout on page
  - Terms acceptance
  - Already registered link

---

## 👨‍💼 Admin Panel Features

### 1. **Dashboard** (`/admin-panel/`)
- Overview statistics
- Recent orders
- Recent customers
- Recent books
- **Quick actions:**
  - View book details (popup modal)
  - Customer information
  - Order status

### 2. **Book Management** (`/admin-panel/books/`)
- List all books with details
- Create new book
- Edit book details:
  - Title, Author, ISBN
  - **Stock management** (integer validation, must be > 0)
  - **Price validation** (must be > 0)
  - Description
  - Category selection
  - Publisher selection
- Delete books
- **Admin book detail popup modal** for quick view
- Search and filter books

### 3. **Publisher Management** (`/admin-panel/publishers/`)
- List all publishers
- Create new publisher
- Edit publisher details
- Delete publishers

### 4. **Category Management** (`/admin-panel/categories/`)
- List all categories
- Create new category
- Edit category details
- Delete categories

### 5. **Customer Management** (`/admin-panel/customers/`)
- List all registered customers
- View customer details
- Customer contact information
- View customer's cart (`/admin-panel/cart/<customer_id>/`)
- Edit customer profile

### 6. **Order Management** (`/admin-panel/orders/`)
- List all orders
- View order details (items, amounts)
- Order status tracking
- Filter by status/date
- Order history

### 7. **Payment Management** (`/admin-panel/payments/`)
- List all payments
- Payment status tracking
- Payment method info
- Refund processing
- Filter by status/date

### 8. **Shipment Management** (`/admin-panel/shipments/`)
- Track shipments
- Update shipment status
- Delivery date tracking
- Shipping method info

### 9. **Review Management** (`/admin-panel/reviews/`)
- View all customer reviews
- Rating distribution
- Filter by book/customer/rating
- Moderate reviews if needed
- View review trends

### 10. **AI Agent Console** (`/admin-panel/agent/`)
- Chat interface for AI agent testing
- Send custom commands
- View agent responses
- Test new intents
- Available commands displayed

---

## 🤖 AI Agent Features

### Agent Capabilities

**1. Stock Checking**
- Command: "stock 1", "check book #5"
- Returns: Book title, available quantity
- Tool: `tool_check_book_stock()`

**2. Top-Rated Books**
- Command: "top rated", "best books"
- Returns: List of books sorted by average rating
- Tool: `tool_top_rated_books()`
- Aggregates reviews from comment-rate-service

**3. Add to Cart**
- Command: "add book 3 to cart", "order 2 units of book"
- Parameters: book_id, quantity
- Tool: `tool_add_to_cart()`
- Validates stock before adding

**4. List Books**
- Command: "show books", "list available"
- Returns: All available books with titles and prices
- Tool: Queries book-service

**5. View Cart**
- Command: "my cart", "view cart"
- Returns: Current cart items with quantities
- Tool: `tool_view_cart()`

**6. Help Command**
- Command: "help", "?"
- Returns: List of available commands with descriptions

### Intent Recognition
The AI agent uses pattern matching to recognize user intents:
- `add_to_cart_pattern`: Matches add/order/buy commands
- `check_stock_pattern`: Matches stock/availability queries
- `top_rated_pattern`: Matches rating/best/top commands
- `list_books_pattern`: Matches list/show/browse commands
- `view_cart_pattern`: Matches cart/view commands

### Conversation History
- All messages stored in `AgentMessage` model
- Per-customer conversation tracking
- Intent tagging for analytics
- Full message history available for context

### API Endpoints
- `POST /api/agent/chat/` - Send message to agent
- `GET /api/agent/help/` - Get available commands
- `GET /admin-panel/agent/` - Web UI for agent console

---

## 📡 API Endpoints

### Authentication Endpoints
```
POST   /api/auth/register/          - User registration
POST   /api/auth/login/             - User login (returns access + refresh tokens)
POST   /api/auth/refresh/           - Refresh access token
POST   /api/auth/logout/            - Logout (blacklist token)
GET    /api/auth/profile/           - Get current user profile
PUT    /api/auth/profile/           - Update user profile
```

### Book Management Endpoints
```
GET    /api/proxy/books/            - List all books (with pagination, filtering, sorting)
POST   /api/proxy/books/            - Create new book (admin only)
GET    /api/proxy/books/<id>/       - Get book details
PUT    /api/proxy/books/<id>/       - Update book (admin only)
DELETE /api/proxy/books/<id>/       - Delete book (admin only)
PATCH  /api/proxy/books/<id>/       - Partial update (e.g., reduce stock)

GET    /api/proxy/categories/       - List categories
POST   /api/proxy/categories/       - Create category (admin only)
GET    /api/proxy/categories/<id>/  - Get category
PUT    /api/proxy/categories/<id>/  - Update category
DELETE /api/proxy/categories/<id>/  - Delete category

GET    /api/proxy/publishers/       - List publishers
POST   /api/proxy/publishers/       - Create publisher (admin only)
GET    /api/proxy/publishers/<id>/  - Get publisher
PUT    /api/proxy/publishers/<id>/  - Update publisher
DELETE /api/proxy/publishers/<id>/  - Delete publisher
```

### Cart Endpoints
```
GET    /api/proxy/carts/<customer_id>/           - Get cart items
POST   /api/proxy/carts/                         - Create cart
POST   /api/proxy/cart-items/                    - Add item to cart
PATCH  /api/proxy/cart-items/<item_id>/         - Update item quantity
DELETE /api/proxy/cart-items/<item_id>/         - Remove item
DELETE /api/proxy/carts/<customer_id>/          - Clear cart
```

### Order Endpoints
```
GET    /api/proxy/orders/                       - List all orders
POST   /api/proxy/orders/                       - Create new order
  Request body:
  {
    "customer_id": 1,
    "payment_method": "cod",           # or "bank_transfer", "credit_card"
    "shipping_method": "standard"
  }

GET    /api/proxy/orders/<id>/                  - Get order details
PATCH  /api/proxy/orders/<id>/                  - Update order status
DELETE /api/proxy/orders/<id>/                  - Cancel order

# Response on successful order:
{
  "id": 1,
  "customer_id": 1,
  "status": "confirmed",
  "total_amount": "499.99",
  "payment_method": "cod",
  "items": [...],
  "message": "Order created and cart cleared"
}

# Response on insufficient stock (409 CONFLICT):
{
  "error": "Insufficient stock for one or more items",
  "insufficient_items": [
    {
      "book_id": 1,
      "title": "Book Title",
      "requested": 5,
      "available": 2,
      "reason": "Not enough inventory"
    }
  ]
}
```

### Payment Endpoints
```
GET    /api/proxy/payments/                     - List payments
POST   /api/proxy/payments/                     - Create payment record
GET    /api/proxy/payments/<id>/                - Get payment
PATCH  /api/proxy/payments/<id>/                - Update payment status
```

### Shipment Endpoints
```
GET    /api/proxy/shipments/                    - List shipments
POST   /api/proxy/shipments/                    - Create shipment
GET    /api/proxy/shipments/<id>/               - Get shipment
PATCH  /api/proxy/shipments/<id>/               - Update shipment
```

### Review/Rating Endpoints
```
GET    /api/proxy/reviews/                      - List all reviews (with filtering)
  Query params:
    - book_id: Filter by specific book
    - customer_id: Filter by customer
    - rating: Filter by rating (1-5)

POST   /api/proxy/reviews/                      - Create new review
  Request body:
  {
    "book_id": 1,
    "customer_id": 1,
    "rating": 5,
    "comment": "Great book!"
  }

GET    /api/proxy/reviews/<id>/                 - Get review
PUT    /api/proxy/reviews/<id>/                 - Update review
DELETE /api/proxy/reviews/<id>/                 - Delete review
```

### Customer Endpoints
```
GET    /api/proxy/customers/                    - List customers (admin)
POST   /api/proxy/customers/                    - Create customer
GET    /api/proxy/customers/<id>/               - Get customer profile
PUT    /api/proxy/customers/<id>/               - Update customer profile
DELETE /api/proxy/customers/<id>/               - Delete customer
```

### AI Agent Endpoints
```
POST   /api/agent/chat/                         - Send message to AI agent
  Request body:
  {
    "message": "add book 1 to cart",
    "customer_id": 1
  }
  
  Response:
  {
    "intent": "add_to_cart",
    "response": "Added 1 copy to your cart",
    "tool_result": {
      "status": "success",
      "message": "Item added to cart"
    }
  }

GET    /api/agent/help/                         - Get available commands
```

### Proxy Endpoints
```
GET    /api/proxy/<service>/                    - List items from service
POST   /api/proxy/<service>/                    - Create item in service
GET    /api/proxy/<service>/<path>/             - Get specific item
PUT    /api/proxy/<service>/<path>/             - Update item
DELETE /api/proxy/<service>/<path>/             - Delete item

# Available services:
books, publishers, categories, customers, carts, cart-items, orders,
payments, shipments, reviews, staff, managers, recommendations, clothes
```

### Health Check Endpoints
```
GET    /health/live/                            - Liveness probe (always 200)
  Response: {"status": "live"}

GET    /health/ready/                           - Readiness probe (checks all services)
  Response: {
    "status": "ready",
    "checks": {
      "auth": true,
      "book": true,
      "cart": true,
      "order": true,
      "payment": true,
      "shipping": true,
      "customer": true,
      "clothes": true
    }
  }
```

---

## 🚀 Setup & Installation

### Prerequisites
- **Docker** and **Docker Compose** (latest version)
- **Python 3.11+** (if running locally without Docker)
- **MySQL 8.0+** on host machine (database)
- **Node.js** (optional, for frontend build tools)

### Database Setup

#### 1. Create MySQL Databases
Connect to MySQL and run:
```sql
-- Auth Database
CREATE DATABASE bookstore_auth CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_auth.* TO 'bookstore_user'@'%' IDENTIFIED BY 'mattroi010';

-- Book Database
CREATE DATABASE bookstore_book CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_book.* TO 'bookstore_user'@'%';

-- Cart Database
CREATE DATABASE bookstore_cart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_cart.* TO 'bookstore_user'@'%';

-- Order Database
CREATE DATABASE bookstore_order CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_order.* TO 'bookstore_user'@'%';

-- Payment Database
CREATE DATABASE bookstore_payment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_payment.* TO 'bookstore_user'@'%';

-- Shipping Database
CREATE DATABASE bookstore_shipment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_shipment.* TO 'bookstore_user'@'%';

-- Customer Database
CREATE DATABASE bookstore_customer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_customer.* TO 'bookstore_user'@'%';

-- Catalog Database
CREATE DATABASE bookstore_catalog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_catalog.* TO 'bookstore_user'@'%';

-- Comment/Rate Database
CREATE DATABASE bookstore_comment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_comment.* TO 'bookstore_user'@'%';

-- Staff Database
CREATE DATABASE bookstore_staff CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_staff.* TO 'bookstore_user'@'%';

-- Manager Database
CREATE DATABASE bookstore_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_manager.* TO 'bookstore_user'@'%';

-- Clothes Database
CREATE DATABASE bookstore_clothes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_clothes.* TO 'bookstore_user'@'%';

-- Recommendation Database
CREATE DATABASE bookstore_recommender CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON bookstore_recommender.* TO 'bookstore_user'@'%';

FLUSH PRIVILEGES;
```

#### 2. Load Sample Data (Optional)
```bash
# Seed bookstore demo data
mysql -u bookstore_user -p bookstore_book < seed_bookstore_demo_data.sql

# Seed staff and manager accounts
python seed_staff_manager.py
```

### Environment Configuration

Each service has environment variables set in `docker-compose.yml`:

```yaml
# Database connection (all services)
DB_HOST=host.docker.internal    # For Docker on Windows/Mac
DB_PORT=3306
DB_USER=bookstore_user
DB_PASSWORD=mattroi010
DB_NAME=bookstore_<service>

# JWT Security
JWT_SECRET=bookstore-jwt-secret
JWT_ALGORITHM=HS256

# Rate Limiting
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_DEFAULT=120         # Default users: 120 req/min
RATE_LIMIT_GUEST=60            # Guest users: 60 req/min
RATE_LIMIT_ADMIN=300           # Admin users: 300 req/min

# RabbitMQ (Optional for event publishing)
RABBITMQ_ENABLED=true
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_EXCHANGE=bookstore.events

# Event Bus (Optional)
EVENT_BUS_URL=
```

---

## 🏃 Running the Project

### Option 1: Docker Compose (Recommended)

#### Start All Services
```bash
cd /path/to/bookstore_micro05

# Build and start all containers
docker compose up -d --build

# Or just start (use existing images)
docker compose up -d

# Check service status
docker compose ps

# View logs for a specific service
docker compose logs -f api-gateway

# View logs for all services
docker compose logs -f
```

#### Stop Services
```bash
docker compose down

# Remove volumes (database data)
docker compose down -v
```

#### Access Services

| Service | URL | Port |
|---------|-----|------|
| API Gateway | http://localhost:8000 | 8000 |
| Auth Service | http://localhost:8012/api/... | 8012 |
| Book Service | http://localhost:8002/api/... | 8002 |
| Cart Service | http://localhost:8003/api/... | 8003 |
| Order Service | http://localhost:8004/api/... | 8004 |
| Payment Service | http://localhost:8009/api/... | 8009 |
| Shipping Service | http://localhost:8007/api/... | 8007 |
| Customer Service | http://localhost:8001/api/... | 8001 |
| RabbitMQ Admin | http://localhost:15672 | 15672 |

#### Default RabbitMQ Credentials
- Username: `guest`
- Password: `guest`

### Option 2: Manual Setup (Local Development)

#### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies per Service
```bash
# Auth Service
cd auth-service
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8012

# In separate terminals, repeat for other services:
# cd book-service && pip install -r requirements.txt && python manage.py migrate && python manage.py runserver 8002
# cd cart-service && ...
# etc.
```

#### 3. Run API Gateway
```bash
cd api-gateway
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

#### 4. Access in Browser
- Homepage: http://localhost:8000
- Admin Panel: http://localhost:8000/admin-panel/
- Login: http://localhost:8000/store/login/

---

## 🛠️ Technology Stack

### Backend
- **Framework:** Django 4.x + Django REST Framework
- **Language:** Python 3.11
- **Database:** MySQL 8.0
- **Authentication:** JWT (PyJWT)
- **Message Queue:** RabbitMQ
- **Web Server:** Django Development Server / Gunicorn (production)

### Frontend
- **Template Engine:** Django Templates
- **CSS Framework:** Bootstrap 5
- **JavaScript:** Vanilla JS + jQuery (legacy)
- **HTTP Client:** Fetch API + Axios (in modals)
- **UI Components:** Bootstrap modals, cards, forms

### DevOps
- **Containerization:** Docker
- **Orchestration:** Docker Compose
- **Database:** MySQL 8.0

### Architecture Patterns
- **API Gateway Pattern** - Centralized entry point
- **Microservices Architecture** - Independent services
- **Saga Pattern** - Distributed transactions (Orders)
- **Event Sourcing** - SagaEvent model + RabbitMQ
- **RBAC** - Role-based access control at gateway
- **Circuit Breaker** - Implicit via timeouts

### Key Libraries
```
Django==4.2
djangorestframework==3.14
PyJWT==2.8
requests==2.31
pika==1.3.2  # RabbitMQ
gunicorn==21.2
mysql-connector-python==8.1
```

---

## 📁 Project Structure

```
bookstore_micro05/
├── README_FULL.md                          # This file
├── docker-compose.yml                      # Service orchestration
├── .env                                    # Environment variables
│
├── api-gateway/                            # Main API Gateway + Web UI
│   ├── api_gateway/
│   │   ├── views.py                       # Request routing, template rendering
│   │   ├── urls.py                        # URL configuration
│   │   ├── settings.py                    # Django settings
│   ├── templates/
│   │   ├── store/                         # User storefront templates
│   │   │   ├── store_base.html           # Master template
│   │   │   ├── store_home.html           # Homepage
│   │   │   ├── store_books.html          # Book catalog
│   │   │   ├── store_book_detail.html    # Book details
│   │   │   ├── store_cart.html           # Shopping cart
│   │   │   ├── store_orders.html         # Order history
│   │   │   ├── store_reviews.html        # Reviews tab
│   │   │   ├── store_login.html          # Login form
│   │   │   ├── store_register.html       # Registration form
│   │   ├── admin/                         # Admin panel templates
│   │   │   ├── dashboard.html            # Admin overview
│   │   │   ├── books.html                # Book CRUD
│   │   │   ├── orders.html               # Order management
│   │   │   ├── payments.html             # Payment tracking
│   │   │   ├── customers.html            # Customer management
│   │   │   ├── agent_chat.html           # AI agent console
│   │   │   └── ...
│   ├── static/                           # CSS, JS, images
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
│
├── auth-service/                          # User Authentication
│   ├── app/
│   │   ├── models.py                     # User model
│   │   ├── views.py                      # Auth endpoints
│   │   ├── serializers.py                # Data validation
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
│
├── book-service/                          # Book Catalog
│   ├── app/
│   │   ├── models.py                     # Book, Publisher, Category
│   │   ├── views.py                      # CRUD operations
│   │   ├── serializers.py               # Validation (stock, price)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
│
├── cart-service/                          # Shopping Cart
│   ├── app/
│   │   ├── models.py                     # Cart, CartItem
│   │   ├── views.py                      # Add/update/remove items
│   │   ├── serializers.py                # Stock validation
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
│
├── order-service/                         # Order Management
│   ├── app/
│   │   ├── models.py                     # Order, OrderItem, SagaEvent
│   │   ├── views.py                      # Order creation with stock checks
│   │   ├── serializers.py                # Order validation
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
│
├── pay-service/                           # Payment Processing
│   ├── app/
│   │   ├── models.py                     # Payment (COD, bank_transfer, etc.)
│   │   ├── views.py                      # Payment endpoints
│   │   ├── serializers.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
│
├── ship-service/                          # Shipping Management
│   ├── app/
│   │   ├── models.py                     # Shipment
│   │   ├── views.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
│
├── customer-service/                      # Customer & AI Agent
│   ├── app/
│   │   ├── models.py                     # Customer, AgentConversation, AgentMessage
│   │   ├── views.py                      # Chat endpoints
│   │   ├── agent.py                      # AI intent recognition & tools
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
│
├── comment-rate-service/                  # Reviews & Ratings
│   ├── app/
│   │   ├── models.py                     # Review
│   │   ├── views.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
│
├── catalog-service/                       # Advanced Catalog
├── recommender-ai-service/                # Book Recommendations
├── staff-service/                         # Staff Management
├── manager-service/                       # Manager Operations
├── clothes-service/                       # Clothing Catalog
│
├── seed_bookstore_demo_data.sql           # Sample book data
├── seed_staff_manager.py                  # Create admin accounts
├── ACTIVE_DATABASE_SCHEMA.sql             # Database schemas
└── BaoCaoKyThuat_BookStore_Microservices.md  # Technical report
```

---

## 🔒 Security Features

### Authentication & Authorization
- **JWT Tokens** - Stateless authentication
- **Access + Refresh Tokens** - Token rotation for security
- **Token Expiration** - Configurable TTL
- **RBAC** - Role-based access control at gateway
- **Service-level Policies** - Fine-grained permission control

### Data Protection
- **Password Hashing** - bcrypt hashing for user passwords
- **HTTPS Ready** - Can be deployed behind SSL/TLS proxy
- **Exception Handling** - Graceful error responses
- **Rate Limiting** - Prevent brute force attacks

### Roles
- **guest** - Unauthenticated users (limited access)
- **customer** - Regular user (browse, order, review)
- **staff** - Staff member (order fulfillment)
- **manager** - Manager level (analytics, staff management)
- **admin** - Administrator (full system access)

---

## 🧪 Testing

### Health Checks
```bash
# API Gateway liveness
curl http://localhost:8000/health/live/

# API Gateway readiness (checks all services)
curl http://localhost:8000/health/ready/
```

### Sample API Calls

#### 1. User Registration
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "securepass123",
    "full_name": "John Doe"
  }'
```

#### 2. User Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "securepass123"
  }'

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLC...",
  "refresh": "eyJ0eXAiOiJKV1QiLC..."
}
```

#### 3. Get Books
```bash
curl http://localhost:8000/api/proxy/books/ \
  -H "Authorization: Bearer <access_token>"
```

#### 4. Add to Cart
```bash
curl -X POST http://localhost:8000/api/proxy/cart-items/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "cart_id": 1,
    "book_id": 1,
    "quantity": 2
  }'
```

#### 5. Place Order
```bash
curl -X POST http://localhost:8000/api/proxy/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "customer_id": 1,
    "payment_method": "cod",
    "shipping_method": "standard"
  }'
```

#### 6. AI Agent Chat
```bash
curl -X POST http://localhost:8000/api/agent/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "message": "show me books with rating 5",
    "customer_id": 1
  }'
```

#### 7. Create Review
```bash
curl -X POST http://localhost:8000/api/proxy/reviews/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "book_id": 1,
    "customer_id": 1,
    "rating": 5,
    "comment": "Excellent book!"
  }'
```

---

## 📈 Performance & Scalability

### Current Architecture
- **Horizontal Scaling** - Each service runs in separate container
- **Independent Databases** - No shared bottleneck
- **Connection Pooling** - Django ORM pooling
- **Rate Limiting** - Prevents abuse
- **Async Events** - RabbitMQ for asynchronous processing

### Optimization Tips
1. **Database Indexing** - Add indexes on frequently queried columns
2. **Caching** - Implement Redis for book catalog caching
3. **CDN** - Serve static files from CDN
4. **Load Balancer** - Use Nginx/HAProxy for load distribution
5. **Connection Pool** - Increase MySQL max connections if needed
6. **Query Optimization** - Add `select_related()` and `prefetch_related()`

---

## 🐛 Troubleshooting

### Container Issues
```bash
# View container logs
docker compose logs api-gateway

# Rebuild specific service
docker compose up -d --build api-gateway

# Check container status
docker ps

# Exec into container for debugging
docker exec -it api-gateway bash

# Restart service
docker compose restart api-gateway
```

### Database Issues
```bash
# Check MySQL connection
docker exec -it mysql mysql -u bookstore_user -p bookstore_book -e "SELECT 1;"

# Reset databases
docker compose down -v
docker compose up -d
```

### Common Errors
1. **"Connection refused"** - Service not started yet, wait 10-15 seconds
2. **"Permission denied"** - Check RBAC roles for user
3. **"Insufficient stock"** - Cart item quantity exceeds available inventory
4. **"Invalid token"** - Token expired or tampered, login again
5. **"Database not found"** - Run migrations for the service

---

## 📝 Notes

- **Demo Credentials:** Check `seed_staff_manager.py` for admin accounts
- **Default JWT Secret:** `bookstore-jwt-secret` (change in production)
- **Database Host:** `host.docker.internal` for Docker containers on Windows/Mac
- **RabbitMQ:** Optional - system works without it using SagaEvents table
- **Rate Limits:** Configurable via environment variables
- **Time Zone:** All timestamps in UTC

---

## 🤝 Contributing

This is an educational project for Assignment 05 & 06. To contribute:
1. Create a feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request with documentation

---

## 📄 License

This project is part of an educational assignment. Usage rights as per institutional policies.

---

## 📞 Support

For issues, questions, or suggestions:
- Check logs: `docker compose logs <service>`
- Review health: `curl http://localhost:8000/health/ready/`
- Verify APIs: Test using provided curl examples
- Check database: Query service databases directly

---

## 🎓 Learning Resources

### Microservices Concepts
- API Gateway Pattern - Centralized routing and auth
- Saga Pattern - Distributed transaction management
- Event Sourcing - Event-based architecture
- Circuit Breaker - Failure resilience
- RBAC - Role-based access control

### Tech Stack Resources
- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Docker: https://docs.docker.com/
- MySQL: https://dev.mysql.com/doc/
- RabbitMQ: https://www.rabbitmq.com/documentation.html

---

## 🎯 Future Enhancements

- [ ] Implement Redis caching layer
- [ ] Add email notifications for orders
- [ ] Implement advanced recommendation ML model
- [ ] Add payment gateway integration (Stripe, PayPal)
- [ ] Implement real-time notifications (WebSocket)
- [ ] Add inventory alerts for low stock
- [ ] Implement order return/refund system
- [ ] Add multi-language support
- [ ] Implement advanced search with Elasticsearch
- [ ] Add GraphQL API alongside REST

---

**Last Updated:** March 31, 2026  
**Project Version:** 1.0  
**Status:** Fully Operational

