#!/usr/bin/env python3
"""
Improved database cleanup: Drop Django tables by disabling foreign key constraints
"""
import mysql.connector

config = {
    'host': 'localhost',
    'user': 'bookstore_user',
    'password': 'mattroi010'
}

# Django system tables to drop (safe to remove from service databases)
DJANGO_SYSTEM_TABLES = [
    'auth_user_user_permissions',
    'auth_user_groups',
    'auth_group_permissions',
    'auth_user',
    'auth_group',
    'auth_permission',
    'django_admin_log',
    'django_content_type',
    'django_session',
    'django_migrations',
]

DATABASES = [
    'bookstore_auth', 'bookstore_book', 'bookstore_cart', 'bookstore_catalog',
    'bookstore_clothes', 'bookstore_comment_rate', 'bookstore_customer',
    'bookstore_gateway', 'bookstore_manager', 'bookstore_order',
    'bookstore_pay', 'bookstore_recommender', 'bookstore_ship', 'bookstore_staff'
]

def drop_django_tables():
    """Drop Django system tables by disabling foreign key constraints"""
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("COMPREHENSIVE DATABASE CLEANUP - Using FK Constraint Disabling")
    print("=" * 80)
    
    for db_name in DATABASES:
        try:
            cursor.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
            if not cursor.fetchone():
                continue
            
            print(f"\nProcessing {db_name}...")
            cursor.execute(f"USE `{db_name}`")
            
            # Disable foreign key constraint checks
            cursor.execute("SET FOREIGN_KEY_CHECKS=0")
            
            # Drop Django system tables
            dropped_count = 0
            for table in DJANGO_SYSTEM_TABLES:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
                    print(f"  ✓ Dropped {table}")
                    dropped_count += 1
                except Exception as e:
                    print(f"  ✗ Error dropping {table}: {e}")
            
            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")
            conn.commit()
            
            if dropped_count > 0:
                print(f"  → Successfully dropped {dropped_count} tables from {db_name}")
        except Exception as e:
            print(f"✗ Error processing {db_name}: {e}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✓ Database cleanup completed!")
    print("=" * 80)

if __name__ == "__main__":
    drop_django_tables()
