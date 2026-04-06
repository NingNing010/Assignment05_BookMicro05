#!/usr/bin/env python3
"""
Create user accounts in bookstore_auth.app_useraccount
matching all customers from bookstore_customer.app_customer
Password: 123456
"""
import mysql.connector

config = {
    'host': 'localhost',
    'user': 'bookstore_user',
    'password': 'mattroi010'
}

DEFAULT_PASSWORD = '123456'
# PBKDF2 hashed password generated from Django shell
HASHED_PASSWORD = "pbkdf2_sha256$600000$MNAxCmWateO7PDqJQ6C01x$vst57dYUwrucoqUjkspWURqIQY+z/qm9Qo0BTKcSJs0="

print(f"Password to use: {DEFAULT_PASSWORD}")
print(f"Hashed password: {HASHED_PASSWORD[:50]}...")
print("=" * 80)

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Step 1: Get all customers with their email and full_name
cursor.execute("USE bookstore_customer")
cursor.execute("SELECT id, full_name, email FROM app_customer")
customers = cursor.fetchall()

print(f"\nFound {len(customers)} customers to create accounts for:")
print("-" * 80)

# Step 2: Create user accounts in bookstore_auth
cursor.execute("USE bookstore_auth")

created_count = 0
skipped_count = 0

for customer_id, full_name, email in customers:
    # Check if user already exists
    cursor.execute("SELECT id FROM app_useraccount WHERE email = %s", (email,))
    existing = cursor.fetchone()
    
    if existing:
        print(f"⊘ SKIP: {email} (already exists)")
        skipped_count += 1
        continue
    
    # Insert new user account
    try:
        cursor.execute("""
            INSERT INTO app_useraccount 
            (email, password, full_name, role, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """, (email, HASHED_PASSWORD, full_name, 'customer', True))
        
        conn.commit()
        print(f"✓ CREATED: {email} ({full_name})")
        created_count += 1
        
    except Exception as e:
        print(f"✗ ERROR: {email} - {e}")
        conn.rollback()

conn.close()

print("-" * 80)
print(f"\nSummary:")
print(f"  ✓ Created: {created_count} new accounts")
print(f"  ⊘ Skipped: {skipped_count} existing accounts")
print(f"  Total: {len(customers)} customers processed")
print("\n" + "=" * 80)
print("All user accounts created successfully!")
print(f"Login with any customer email + password: {DEFAULT_PASSWORD}")
