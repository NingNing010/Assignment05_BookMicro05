import mysql.connector

config = {
    "host": "localhost",
    "user": "bookstore_user",
    "password": "mattroi010",
}

staff_rows = [
    (1, "Nguyen Van Staff", "staff01@bookstore.vn", "sales_staff"),
    (2, "Tran Thi Support", "staff02@bookstore.vn", "support_staff"),
    (3, "Le Quoc Kho", "staff03@bookstore.vn", "warehouse_staff"),
    (4, "Pham Thu CSKH", "staff04@bookstore.vn", "customer_service"),
]

manager_rows = [
    (1, "Nguyen Minh Quan", "manager01@bookstore.vn", "operations"),
    (2, "Tran Bao Chau", "manager02@bookstore.vn", "sales"),
    (3, "Le Hoang Nam", "manager03@bookstore.vn", "customer_success"),
]

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

cursor.execute("USE bookstore_staff")
for row in staff_rows:
    cursor.execute(
        """
        INSERT INTO app_staff (id, name, email, role)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          name = VALUES(name),
          email = VALUES(email),
          role = VALUES(role)
        """,
        row,
    )

cursor.execute("USE bookstore_manager")
for row in manager_rows:
    cursor.execute(
        """
        INSERT INTO app_manager (id, name, email, department)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          name = VALUES(name),
          email = VALUES(email),
          department = VALUES(department)
        """,
        row,
    )

conn.commit()

cursor.execute("SELECT COUNT(*) FROM bookstore_staff.app_staff")
staff_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM bookstore_manager.app_manager")
manager_count = cursor.fetchone()[0]

print(f"Seeded app_staff successfully. Current rows: {staff_count}")
print(f"Seeded app_manager successfully. Current rows: {manager_count}")

cursor.close()
conn.close()
