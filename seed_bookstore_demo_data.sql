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
  (4, 'DevOps', 'Deployment, CI/CD, cloud and operations'),
  (5, 'Cooking', 'Cooking, recipes and culinary skills'),
  (6, 'Lifestyle', 'Self-help, habits and healthy living'),
  (7, 'Household', 'Home organization and useful household guides'),
  (8, 'Business', 'Business, sales, marketing and finance'),
  (9, 'Children', 'Books for kids and parenting')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  description = VALUES(description);

INSERT INTO app_publisher (id, name, address, email) VALUES
  (1, 'TechBooks VN', 'Ho Chi Minh City', 'contact@techbooksvn.com'),
  (2, 'Global Code Press', 'Singapore', 'hello@globalcodepress.io'),
  (3, 'Cloud Native House', 'Ha Noi', 'support@cloudnativehouse.vn'),
  (4, 'LifeStyle Press', 'Da Nang', 'hello@lifestylepress.vn'),
  (5, 'Family & Home Books', 'Can Tho', 'support@familyhomebooks.vn')
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
  (6, 'The DevOps Handbook', 'Gene Kim', 390000.00, 35, 'How to create world-class agility and reliability', '9781942788003', 4, 3),
  (12, 'Nau An Viet Nam De Dang', 'Chef Minh Anh', 240000.00, 40, 'Cong thuc mon Viet don gian cho nguoi moi bat dau', '9786041234501', 5, 4),
  (13, 'Healthy Meal Prep', 'Luna Nguyen', 260000.00, 28, 'Huong dan meal prep va thuc don can bang cho ca tuan', '9786041234502', 5, 4),
  (14, 'Song Toi Gian Hieu Qua', 'Tran Hoang', 210000.00, 33, 'Toi gian hoa doi song va cai thien chat luong song', '9786041234503', 6, 4),
  (15, 'Atomic Habits Thuc Hanh', 'James Clear VN', 295000.00, 22, 'Xay dung thoi quen tot va pha vo thoi quen xau', '9786041234504', 6, 4),
  (16, 'Nha Cua Gon Gang Moi Ngay', 'Ngoc Ha', 185000.00, 30, 'Giai phap sap xep, don dep va quan ly vat dung trong nha', '9786041234505', 7, 5),
  (17, 'Do Gia Dung Thong Minh', 'Khanh Ly', 230000.00, 18, 'Cam nang chon va su dung vat dung gia dung hieu qua', '9786041234506', 7, 5),
  (18, 'Khoi Nghiep Tinh Gon', 'Pham Quang', 320000.00, 20, 'Tu y tuong den mo hinh kinh doanh cho startup nho', '9786041234507', 8, 4),
  (19, 'Marketing 0 Dong', 'Le Nhat Linh', 275000.00, 26, 'Chien luoc marketing chi phi thap cho doanh nghiep nho', '9786041234508', 8, 4),
  (20, 'Truyen Ke Be Ngu', 'Bao An', 165000.00, 45, 'Tuyen tap truyen ngan cho tre em truoc gio di ngu', '9786041234509', 9, 5),
  (21, 'Nuoi Day Con Tu Som', 'Thu Ha', 250000.00, 24, 'Kien thuc nen tang ve giao duc som cho tre nho', '9786041234510', 9, 5)
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
  (4, 'DevOps', 'Deployment, CI/CD, cloud and operations'),
  (5, 'Cooking', 'Cooking, recipes and culinary skills'),
  (6, 'Lifestyle', 'Self-help, habits and healthy living'),
  (7, 'Household', 'Home organization and useful household guides'),
  (8, 'Business', 'Business, sales, marketing and finance'),
  (9, 'Children', 'Books for kids and parenting')
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

-- 7) STAFF SERVICE DATA
USE bookstore_staff;

INSERT INTO app_staff (id, name, email, role) VALUES
  (1, 'Nguyen Van Staff', 'staff01@bookstore.vn', 'sales_staff'),
  (2, 'Tran Thi Support', 'staff02@bookstore.vn', 'support_staff'),
  (3, 'Le Quoc Kho', 'staff03@bookstore.vn', 'warehouse_staff'),
  (4, 'Pham Thu CSKH', 'staff04@bookstore.vn', 'customer_service')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  email = VALUES(email),
  role = VALUES(role);

-- 8) MANAGER SERVICE DATA
USE bookstore_manager;

INSERT INTO app_manager (id, name, email, department) VALUES
  (1, 'Nguyen Minh Quan', 'manager01@bookstore.vn', 'operations'),
  (2, 'Tran Bao Chau', 'manager02@bookstore.vn', 'sales'),
  (3, 'Le Hoang Nam', 'manager03@bookstore.vn', 'customer_success')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  email = VALUES(email),
  department = VALUES(department);

-- 9) Quick checks
SELECT COUNT(*) AS books_count FROM bookstore_book.app_book;
SELECT COUNT(*) AS customers_count FROM bookstore_customer.app_customer;
SELECT COUNT(*) AS clothes_count FROM bookstore_clothes.app_clothes;
SELECT COUNT(*) AS staff_count FROM bookstore_staff.app_staff;
SELECT COUNT(*) AS manager_count FROM bookstore_manager.app_manager;
