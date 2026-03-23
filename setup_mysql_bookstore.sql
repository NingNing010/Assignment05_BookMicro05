-- =========================================
-- BookStore Microservices - MySQL Setup
-- Run as MySQL root user
-- =========================================

SET NAMES utf8mb4;

-- 1) Create databases (one DB per service)
CREATE DATABASE IF NOT EXISTS bookstore_customer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_book CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_cart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_staff CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_catalog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_order CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_ship CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_pay CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_comment_rate CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_recommender CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_gateway CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_auth CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS bookstore_clothes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2) Create dedicated application user
-- You can change password if needed
CREATE USER IF NOT EXISTS 'bookstore_user'@'%' IDENTIFIED BY 'mattroi010';
CREATE USER IF NOT EXISTS 'bookstore_user'@'localhost' IDENTIFIED BY 'mattroi010';

-- 3) Grant permissions only to BookStore databases
GRANT ALL PRIVILEGES ON bookstore_customer.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_book.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_cart.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_staff.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_manager.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_catalog.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_order.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_ship.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_pay.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_comment_rate.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_recommender.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_gateway.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_auth.* TO 'bookstore_user'@'%';
GRANT ALL PRIVILEGES ON bookstore_clothes.* TO 'bookstore_user'@'%';

GRANT ALL PRIVILEGES ON bookstore_customer.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_book.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_cart.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_staff.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_manager.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_catalog.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_order.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_ship.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_pay.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_comment_rate.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_recommender.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_gateway.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_auth.* TO 'bookstore_user'@'localhost';
GRANT ALL PRIVILEGES ON bookstore_clothes.* TO 'bookstore_user'@'localhost';

FLUSH PRIVILEGES;

-- 4) Verification
SHOW DATABASES LIKE 'bookstore_%';
SHOW GRANTS FOR 'bookstore_user'@'%';
SHOW GRANTS FOR 'bookstore_user'@'localhost';
