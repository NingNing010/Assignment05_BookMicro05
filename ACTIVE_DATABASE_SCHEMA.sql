-- =========================================
-- BookStore Database - Active Schema Reference
-- After cleanup and optimization
-- Run: March 31, 2026
-- =========================================

-- Current state: 34 production tables across 14 service databases
-- All Django system tables removed (140 table deletions)

USE bookstore_auth;
-- Table: app_useraccount
-- - Custom user authentication model
-- - Columns: id, email, password, full_name, role, is_active, created_at, updated_at

USE bookstore_book;
-- Table: app_book
-- - Books catalog (11 books after enhancement)
-- - Columns: id, title, author, price, stock, description, isbn, category_id, publisher_id
-- Table: app_category
-- - Book categories (4 categories)
-- - Columns: id, name, description
-- Table: app_publisher
-- - Publisher information (3 publishers)
-- - Columns: id, name, address, email

USE bookstore_cart;
-- Table: app_cart
-- - Shopping carts (customer ID based)
-- - Columns: id, customer_id
-- Table: app_cartitem
-- - Items in carts
-- - Columns: id, cart_id, book_id, quantity

USE bookstore_catalog;
-- Table: app_category
-- - Catalog categories (mirrors book_service categories)
-- - Columns: id, name, description

USE bookstore_clothes;
-- Table: app_clothes
-- - Clothing inventory (8 items after enhancement)
-- - Columns: id, name, brand, size, color, price, stock, description

USE bookstore_comment_rate;
-- Table: app_review
-- - Product reviews and ratings (15+ reviews after enhancement)
-- - Columns: id, book_id, customer_id, rating, comment, created_at

USE bookstore_customer;
-- Table: app_customer
-- - Customer profiles (8 customers after enhancement)
-- - Columns: id, name, full_name, email, phone, address
-- Table: app_agentconversation
-- - AI agent conversation history per customer
-- - Columns: id, customer_id, created_at
-- Table: app_agentmessage
-- - Conversation messages
-- - Columns: id, conversation_id, role, content, intent, created_at

USE bookstore_gateway;
-- Gateway database (currently empty - no tables)

USE bookstore_manager;
-- Table: app_manager
-- - Manager accounts
-- - Columns: id, name, email, department

USE bookstore_order;
-- Table: app_order
-- - Orders placed by customers
-- - Columns: id, customer_id, status, total_amount, payment_method, shipping_method, created_at
-- Table: app_orderitem
-- - Items in orders
-- - Columns: id, order_id, book_id, quantity, price
-- Table: app_sagaevent
-- - Saga orchestration events for distributed transactions
-- - Columns: id, topic, payload, created_at

USE bookstore_pay;
-- Table: app_payment
-- - Payment transactions (12+ records after enhancement)
-- - Columns: id, order_id, amount, method, status, created_at

USE bookstore_recommender;
-- Table: app_recommendation
-- - AI-generated recommendations (25+ records after enhancement)
-- - Columns: id, customer_id, book_id, score, created_at

USE bookstore_ship;
-- Table: app_shipment
-- - Shipment tracking
-- - Columns: id, order_id, customer_id, method, status, tracking_number, created_at

USE bookstore_staff;
-- Table: app_staff
-- - Staff member accounts
-- - Columns: id, name, email, role

-- =========================================
-- Data Summary
-- =========================================
SELECT 'Books' as `Database`, COUNT(*) as `Record Count` FROM bookstore_book.app_book
UNION ALL
SELECT 'Categories', COUNT(*) FROM bookstore_book.app_category
UNION ALL
SELECT 'Customers', COUNT(*) FROM bookstore_customer.app_customer
UNION ALL
SELECT 'Reviews', COUNT(*) FROM bookstore_comment_rate.app_review
UNION ALL
SELECT 'Clothes', COUNT(*) FROM bookstore_clothes.app_clothes
UNION ALL
SELECT 'Recommendations', COUNT(*) FROM bookstore_recommender.app_recommendation
UNION ALL
SELECT 'Payments', COUNT(*) FROM bookstore_pay.app_payment
UNION ALL
SELECT 'Orders', COUNT(*) FROM bookstore_order.app_order;

-- =========================================
-- Useful Queries
-- =========================================

-- Find orders with customer names
-- SELECT o.id, c.full_name, o.total_amount, o.status
-- FROM bookstore_order.app_order o
-- JOIN bookstore_customer.app_customer c ON c.id = o.customer_id;

-- Get popular books (by review count)
-- SELECT b.title, COUNT(r.id) as review_count, AVG(r.rating) as avg_rating
-- FROM bookstore_book.app_book b
-- LEFT JOIN bookstore_comment_rate.app_review r ON r.book_id = b.id
-- GROUP BY b.id
-- ORDER BY review_count DESC;

-- Find recommendations for a customer
-- SELECT c.full_name, b.title, r.score
-- FROM bookstore_recommender.app_recommendation r
-- JOIN bookstore_customer.app_customer c ON c.id = r.customer_id
-- JOIN bookstore_book.app_book b ON b.id = r.book_id
-- WHERE c.id = 1
-- ORDER BY r.score DESC;
