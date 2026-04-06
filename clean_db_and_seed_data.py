#!/usr/bin/env python3
"""
Analyze databases: identify unused tables and add more sample data
"""
import mysql.connector
from datetime import datetime, timedelta
import random

# Connection config
config = {
    'host': 'localhost',
    'user': 'bookstore_user',
    'password': 'mattroi010'
}

# Map of databases to expected tables (tables that should exist and be used)
EXPECTED_TABLES = {
    'bookstore_auth': ['app_useraccount'],
    'bookstore_book': ['app_book', 'app_category', 'app_publisher'],
    'bookstore_cart': ['app_cart', 'app_cartitem'],
    'bookstore_catalog': ['app_category'],
    'bookstore_clothes': ['app_clothes'],
    'bookstore_comment_rate': ['app_review'],
    'bookstore_customer': ['app_customer', 'app_agentconversation', 'app_agentmessage'],
    'bookstore_gateway': [],  # Gateway DB (may not have tables)
    'bookstore_manager': ['app_manager'],
    'bookstore_order': ['app_order', 'app_orderitem', 'app_sagaevent'],
    'bookstore_pay': ['app_payment'],
    'bookstore_recommender': ['app_recommendation'],
    'bookstore_ship': ['app_shipment'],
    'bookstore_staff': ['app_staff'],
}

def get_tables_in_db(cursor, db_name):
    """Get all tables in a database"""
    cursor.execute(f"USE `{db_name}`")
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def get_connection():
    """Create and return a database connection"""
    return mysql.connector.connect(**config)

def analyze_databases():
    """Analyze all databases for unused tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("DATABASE ANALYSIS - Finding Unused Tables")
    print("=" * 80)
    
    unused_tables = {}
    for db_name, expected_tables in EXPECTED_TABLES.items():
        cursor.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
        if not cursor.fetchone():
            print(f"\n[INFO] Database {db_name} doesn't exist - skipping")
            continue
            
        actual_tables = get_tables_in_db(cursor, db_name)
        unused = [t for t in actual_tables if t not in expected_tables]
        
        print(f"\n{db_name}:")
        print(f"  Expected tables: {expected_tables}")
        print(f"  Actual tables:   {actual_tables}")
        
        if unused:
            print(f"  ❌ UNUSED TABLES found: {unused}")
            unused_tables[db_name] = unused
        else:
            print(f"  ✓ All tables are in use")
    
    conn.close()
    return unused_tables

def drop_unused_tables(unused_tables):
    """Drop all unused tables"""
    if not unused_tables:
        print("\n" + "=" * 80)
        print("No unused tables found!")
        print("=" * 80)
        return
    
    print("\n" + "=" * 80)
    print("DROPPING UNUSED TABLES")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for db_name, tables in unused_tables.items():
        for table in tables:
            try:
                cursor.execute(f"USE `{db_name}`")
                cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
                conn.commit()
                print(f"✓ Dropped {db_name}.{table}")
            except Exception as e:
                print(f"✗ Error dropping {db_name}.{table}: {e}")
    
    conn.close()

def add_more_sample_data():
    """Add more comprehensive sample data"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("ADDING MORE SAMPLE DATA")
    print("=" * 80)
    
    try:
        # 1. BOOK SERVICE - Add more books and publishers
        cursor.execute("USE bookstore_book")
        
        # Check current books count
        cursor.execute("SELECT COUNT(*) FROM app_book")
        book_count = cursor.fetchone()[0]
        print(f"\nBook service: {book_count} books exist")
        
        if book_count < 10:
            print("Adding more books...")
            more_books = [
                ("Building Microservices", "Sam Newman", 480000.00, 25, "Designing fine-grained systems", "9781491950357", 3, 2),
                ("Kubernetes in Action", "Marko Luksa", 520000.00, 15, "Deploy and manage containerized applications", "9781617293726", 4, 2),
                ("Site Reliability Engineering", "Betsy Beyer", 490000.00, 20, "How Google runs production systems", "9781491929881", 4, 3),
                ("Effective Java", "Joshua Bloch", 350000.00, 40, "Programming language guide", "9780134685991", 1, 2),
                ("System Design Interview", "Alex Xu", 420000.00, 30, "Prepare for tech interviews", "9781736049692", 3, 1),
            ]
            for title, author, price, stock, desc, isbn, cat_id, pub_id in more_books:
                cursor.execute("""
                    INSERT INTO app_book (title, author, price, stock, description, isbn, category_id, publisher_id)
                    SELECT %s, %s, %s, %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (SELECT 1 FROM app_book WHERE isbn = %s)
                """, (title, author, price, stock, desc, isbn, cat_id, pub_id, isbn))
            conn.commit()
            print(f"✓ Added {len(more_books)} books")
        
        # 2. CUSTOMER SERVICE - Add more customers
        cursor.execute("USE bookstore_customer")
        cursor.execute("SELECT COUNT(*) FROM app_customer")
        customer_count = cursor.fetchone()[0]
        print(f"\nCustomer service: {customer_count} customers exist")
        
        if customer_count < 8:
            print("Adding more customers...")
            more_customers = [
                ("ngthao", "Nguyen Thi Thao", "thao.nguyen@example.com", "0901000004", "District 3, Ho Chi Minh City"),
                ("minhnq", "Nguyen Quoc Minh", "minh.nq@example.com", "0901000005", "Binh Duong Province"),
                ("hieulv", "Luu Van Hieu", "hieu.lv@example.com", "0901000006", "Da Lat City"),
                ("an2003", "Le Van An", "van.an@example.com", "0901000007", "Nha Trang City"),
                ("khangnm", "Nguyen Minh Khang", "khang.nm@example.com", "0901000008", "Can Tho City"),
            ]
            for name, full_name, email, phone, addr in more_customers:
                cursor.execute("""
                    INSERT INTO app_customer (name, full_name, email, phone, address)
                    SELECT %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (SELECT 1 FROM app_customer WHERE email = %s)
                """, (name, full_name, email, phone, addr, email))
            conn.commit()
            print(f"✓ Added {len(more_customers)} customers")
        
        # 3. COMMENT/RATE SERVICE - Add more reviews
        cursor.execute("USE bookstore_comment_rate")
        cursor.execute("SELECT COUNT(*) FROM app_review")
        review_count = cursor.fetchone()[0]
        print(f"\nComment/Rate service: {review_count} reviews exist")
        
        if review_count < 10:
            print("Adding more reviews...")
            cursor.execute("USE bookstore_book")
            cursor.execute("SELECT id FROM app_book LIMIT 10")
            book_ids = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("USE bookstore_customer")
            cursor.execute("SELECT id FROM app_customer LIMIT 10")
            customer_ids = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("USE bookstore_comment_rate")
            
            comments = [
                "Excellent book, highly recommended!",
                "Very informative and practical",
                "Great for learning the basics",
                "Advanced content, perfect reference",
                "Well-written with good examples",
                "Wish it had more deep dives",
                "Exactly what I needed",
                "Outstanding technical content"
            ]
            
            more_reviews = []
            for i in range(12):
                book_id = book_ids[i % len(book_ids)]
                customer_id = customer_ids[(i + 1) % len(customer_ids)]
                rating = random.randint(3, 5)
                comment = comments[i % len(comments)]
                cursor.execute("""
                    INSERT INTO app_review (book_id, customer_id, rating, comment, created_at)
                    SELECT %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (SELECT 1 FROM app_review WHERE book_id = %s AND customer_id = %s)
                """, (book_id, customer_id, rating, comment, datetime.now(), book_id, customer_id))
            conn.commit()
            print(f"✓ Added more reviews")
        
        # 4. CLOTHES SERVICE - Already has 4 items, add more
        cursor.execute("USE bookstore_clothes")
        cursor.execute("SELECT COUNT(*) FROM app_clothes")
        clothes_count = cursor.fetchone()[0]
        print(f"\nClothes service: {clothes_count} items exist")
        
        if clothes_count < 8:
            print("Adding more clothing items...")
            more_clothes = [
                ("Giay sneaker", "SportStyle", "42", "White", 599000.00, 25, "Giay the thao thoang khí"),
                ("Tui xach da", "LuxeBags", "One Size", "Brown", 899000.00, 10, "Tui xach da that chính hãng"),
                ("Moc luu niem", "AccessVN", "One Size", "Silver", 99000.00, 50, "Trang suc nho xinh"),
                ("Mu nap", "CapStyle", "Free Size", "Black", 179000.00, 30, "Mu cap thoi trang"),
            ]
            for name, brand, size, color, price, stock, desc in more_clothes:
                cursor.execute("""
                    INSERT INTO app_clothes (name, brand, size, color, price, stock, description)
                    SELECT %s, %s, %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (SELECT 1 FROM app_clothes WHERE name = %s AND brand = %s)
                """, (name, brand, size, color, price, stock, desc, name, brand))
            conn.commit()
            print(f"✓ Added {len(more_clothes)} clothing items")
        
        # 5. RECOMMENDER SERVICE - Add more recommendations
        cursor.execute("USE bookstore_recommender")
        cursor.execute("SELECT COUNT(*) FROM app_recommendation")
        rec_count = cursor.fetchone()[0]
        print(f"\nRecommender service: {rec_count} recommendations exist")
        
        if rec_count < 20:
            print("Adding more recommendations...")
            cursor.execute("USE bookstore_book")
            cursor.execute("SELECT id FROM app_book LIMIT 15")
            available_books = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("USE bookstore_customer")
            cursor.execute("SELECT id FROM app_customer LIMIT 15")
            available_customers = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("USE bookstore_recommender")
            
            for i in range(25):
                customer_id = available_customers[i % len(available_customers)]
                book_id = available_books[(i + 2) % len(available_books)]
                score = round(random.uniform(0.5, 1.0), 2)
                cursor.execute("""
                    INSERT INTO app_recommendation (customer_id, book_id, score, created_at)
                    SELECT %s, %s, %s, %s
                    WHERE NOT EXISTS (SELECT 1 FROM app_recommendation WHERE customer_id = %s AND book_id = %s)
                """, (customer_id, book_id, score, datetime.now(), customer_id, book_id))
            conn.commit()
            print(f"✓ Added more recommendations")
        
        # 6. PAYMENT SERVICE - Add more payment records
        cursor.execute("USE bookstore_pay")
        cursor.execute("SELECT COUNT(*) FROM app_payment")
        payment_count = cursor.fetchone()[0]
        print(f"\nPayment service: {payment_count} payment records exist")
        
        if payment_count < 10:
            print("Adding more payment records...")
            methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer']
            statuses = ['pending', 'reserved', 'completed', 'failed']
            
            for i in range(1, 15):
                order_id = i
                amount = round(random.uniform(200000, 2000000), 2)
                method = random.choice(methods)
                status = 'completed' if random.random() > 0.2 else random.choice(statuses)
                cursor.execute("""
                    INSERT INTO app_payment (order_id, amount, method, status, created_at)
                    SELECT %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (SELECT 1 FROM app_payment WHERE order_id = %s)
                """, (order_id, amount, method, status, datetime.now() - timedelta(days=random.randint(0, 30)), order_id))
            conn.commit()
            print(f"✓ Added more payment records")
        
        print("\n" + "=" * 80)
        print("✓ Data enhancement completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("\nBookStore Database Cleanup & Enhancement Tool")
    print("=" * 80)
    
    # Step 1: Analyze
    unused = analyze_databases()
    
    # Step 2: Drop unused tables
    if unused:
        drop_unused_tables(unused)
    
    # Step 3: Add more sample data
    add_more_sample_data()
