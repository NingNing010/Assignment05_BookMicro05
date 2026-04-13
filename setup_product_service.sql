-- =========================================
-- Migration Script: Create bookstore_product database
-- Migrate data from bookstore_book + bookstore_clothes
-- into unified product-service (DDD)
-- =========================================

-- Step 1: Create the new database
CREATE DATABASE IF NOT EXISTS bookstore_product CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant permissions
GRANT ALL PRIVILEGES ON bookstore_product.* TO 'bookstore_user'@'%';
FLUSH PRIVILEGES;

-- =========================================
-- Note: Django migrations (manage.py migrate) will create the tables.
-- After running migrations, run the seed scripts:
--   python manage.py shell < modules/catalog/seeds/categories_seed.py
--   python manage.py shell < modules/catalog/seeds/products_seed.py
-- =========================================

-- Step 2: Update cart-service to rename book_id → product_id
-- (Run this AFTER the cart-service migration)
-- ALTER TABLE bookstore_cart.app_cartitem CHANGE book_id product_id int NOT NULL;
