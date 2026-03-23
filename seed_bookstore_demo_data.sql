-- =========================================
-- BookStore Microservices - Demo Seed Data
-- Idempotent seed: safe to run multiple times
-- =========================================

SET NAMES utf8mb4;

-- 1) BOOK SERVICE DATA
USE bookstore_book;

INSERT INTO app_category (id, name, description) VALUES
  (1, 'Programming', 'Software development and coding books'),
  (2, 'Data Science', 'Machine learning, AI and analytics'),
  (3, 'Architecture', 'Software architecture and system design'),
  (4, 'DevOps', 'Deployment, CI/CD, cloud and operations')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  description = VALUES(description);

INSERT INTO app_publisher (id, name, address, email) VALUES
  (1, 'TechBooks VN', 'Ho Chi Minh City', 'contact@techbooksvn.com'),
  (2, 'Global Code Press', 'Singapore', 'hello@globalcodepress.io'),
  (3, 'Cloud Native House', 'Ha Noi', 'support@cloudnativehouse.vn')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  address = VALUES(address),
  email = VALUES(email);

INSERT INTO app_book (id, title, author, price, stock, description, isbn, category_id, publisher_id) VALUES
  (1, 'Clean Code', 'Robert C. Martin', 320000.00, 50, 'A handbook of agile software craftsmanship', '9780132350884', 1, 2),
  (2, 'Designing Data-Intensive Applications', 'Martin Kleppmann', 450000.00, 30, 'Reliable, scalable, and maintainable systems', '9781449373320', 3, 2),
  (3, 'Microservices Patterns', 'Chris Richardson', 410000.00, 25, 'Patterns for decomposition and data consistency', '9781617294549', 3, 2),
  (4, 'Python Crash Course', 'Eric Matthes', 280000.00, 60, 'Practical introduction to Python', '9781593279288', 1, 1),
  (5, 'Hands-On Machine Learning', 'Aurelien Geron', 520000.00, 20, 'ML with Scikit-Learn, Keras and TensorFlow', '9781492032649', 2, 2),
  (6, 'The DevOps Handbook', 'Gene Kim', 390000.00, 35, 'How to create world-class agility and reliability', '9781942788003', 4, 3)
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  author = VALUES(author),
  price = VALUES(price),
  stock = VALUES(stock),
  description = VALUES(description),
  isbn = VALUES(isbn),
  category_id = VALUES(category_id),
  publisher_id = VALUES(publisher_id);

-- 2) CATALOG SERVICE DATA
USE bookstore_catalog;

INSERT INTO app_category (id, name, description) VALUES
  (1, 'Programming', 'Software development and coding books'),
  (2, 'Data Science', 'Machine learning, AI and analytics'),
  (3, 'Architecture', 'Software architecture and system design'),
  (4, 'DevOps', 'Deployment, CI/CD, cloud and operations')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  description = VALUES(description);

-- 3) CUSTOMER SERVICE DATA
USE bookstore_customer;

INSERT INTO app_customer (id, name, full_name, email, phone, address) VALUES
  (1, 'ninh01', 'Le Dang Ninh', 'ninh01@example.com', '0901000001', 'District 1, Ho Chi Minh City'),
  (2, 'haipham', 'Pham Hai', 'haipham@example.com', '0901000002', 'Go Vap, Ho Chi Minh City'),
  (3, 'dieptran', 'Tran Diep', 'dieptran@example.com', '0901000003', 'Thanh Xuan, Ha Noi')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  full_name = VALUES(full_name),
  email = VALUES(email),
  phone = VALUES(phone),
  address = VALUES(address);

-- 4) CART SERVICE DATA
USE bookstore_cart;

INSERT INTO app_cart (id, customer_id) VALUES
  (1, 1),
  (2, 2),
  (3, 3)
ON DUPLICATE KEY UPDATE
  customer_id = VALUES(customer_id);

INSERT INTO app_cartitem (id, cart_id, book_id, quantity) VALUES
  (1, 1, 1, 1),
  (2, 1, 4, 2),
  (3, 2, 3, 1),
  (4, 3, 5, 1)
ON DUPLICATE KEY UPDATE
  cart_id = VALUES(cart_id),
  book_id = VALUES(book_id),
  quantity = VALUES(quantity);

-- 5) COMMENT/RATE SERVICE DATA
USE bookstore_comment_rate;

INSERT INTO app_review (id, book_id, customer_id, rating, comment, created_at) VALUES
  (1, 1, 1, 5, 'Very practical and useful for code quality.', NOW()),
  (2, 3, 2, 5, 'Great for understanding microservice trade-offs.', NOW()),
  (3, 4, 1, 4, 'Good entry point for Python beginners.', NOW()),
  (4, 5, 3, 5, 'Excellent ML reference with hands-on examples.', NOW())
ON DUPLICATE KEY UPDATE
  book_id = VALUES(book_id),
  customer_id = VALUES(customer_id),
  rating = VALUES(rating),
  comment = VALUES(comment),
  created_at = VALUES(created_at);

-- 6) CLOTHES SERVICE DATA
USE bookstore_clothes;

INSERT INTO app_clothes (id, name, brand, size, color, price, stock, description) VALUES
  (1, 'Ao thun basic', 'Local Brand', 'M', 'Black', 199000.00, 50, 'Cotton 100%, form regular'),
  (2, 'Ao hoodie unisex', 'StreetWear VN', 'L', 'Gray', 459000.00, 20, 'Nỉ da cá, phù hợp thời tiết mát'),
  (3, 'Quan jogger', 'MoveFit', 'M', 'Navy', 349000.00, 35, 'Co giãn tốt, mặc đi học đi làm'),
  (4, 'Ao so mi casual', 'OfficeLab', 'L', 'White', 299000.00, 28, 'Chất liệu thoáng, ít nhăn')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  brand = VALUES(brand),
  size = VALUES(size),
  color = VALUES(color),
  price = VALUES(price),
  stock = VALUES(stock),
  description = VALUES(description);

-- 7) Quick checks
SELECT COUNT(*) AS books_count FROM bookstore_book.app_book;
SELECT COUNT(*) AS customers_count FROM bookstore_customer.app_customer;
SELECT COUNT(*) AS clothes_count FROM bookstore_clothes.app_clothes;
