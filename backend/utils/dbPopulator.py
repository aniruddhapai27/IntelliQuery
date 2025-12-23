from faker import Faker
import random
import mysql.connector
from datetime import datetime, timedelta
import numpy as np

fake = Faker()

# ---------------- DB CONFIG ----------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345",
    database="ecommerce"
)
cursor = conn.cursor()

# ---------------- PARAMETERS ----------------
NUM_CUSTOMERS = 5000
NUM_PRODUCTS = 200
NUM_ORDERS = 10000

CATEGORIES = ["Electronics", "Fashion", "Home", "Sports", "Books"]
STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED"]

# ---------------- CUSTOMERS ----------------
customers = []
for _ in range(NUM_CUSTOMERS):
    customers.append((
        fake.name(),
        fake.email(),
        fake.city(),
        fake.state(),
        fake.country()[:50],
        fake.date_between(start_date="-2y", end_date="today")
    ))

cursor.executemany("""
INSERT INTO customers (name, email, city, state, country, signup_date)
VALUES (%s,%s,%s,%s,%s,%s)
""", customers)
conn.commit()

# ---------------- PRODUCTS ----------------
products = []
for _ in range(NUM_PRODUCTS):
    products.append((
        fake.word().capitalize(),
        random.choice(CATEGORIES),
        round(random.uniform(200, 100000), 2)
    ))

cursor.executemany("""
INSERT INTO products (product_name, category, price)
VALUES (%s,%s,%s)
""", products)
conn.commit()

# ---------------- FETCH CUSTOMER IDS ----------------
cursor.execute("SELECT customer_id FROM customers")
customer_ids = [row[0] for row in cursor.fetchall()]

# ---------------- ORDERS ----------------
orders = []
for _ in range(NUM_ORDERS):
    orders.append((
        random.choice(customer_ids),
        fake.date_between(start_date="-1y", end_date="today"),
        random.choices(STATUSES, weights=[2,3,4,1])[0]
    ))

cursor.executemany("""
INSERT INTO orders (customer_id, order_date, status)
VALUES (%s,%s,%s)
""", orders)
conn.commit()

# ---------------- ORDER ITEMS ----------------
cursor.execute("SELECT order_id FROM orders")
order_ids = [x[0] for x in cursor.fetchall()]

cursor.execute("SELECT product_id, price FROM products")
products_db = cursor.fetchall()

order_items = []

for order_id in order_ids:
    num_items = random.randint(1, 4)
    sampled_products = random.sample(products_db, num_items)

    for product_id, price in sampled_products:
        order_items.append((
            order_id,
            product_id,
            random.randint(1, 5),
            price
        ))

cursor.executemany("""
INSERT INTO order_items (order_id, product_id, quantity, item_price)
VALUES (%s,%s,%s,%s)
""", order_items)
conn.commit()

print("✅ 10K+ records generated successfully")

cursor.close()
conn.close()
