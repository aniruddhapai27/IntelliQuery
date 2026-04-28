import os
from faker import Faker
import random
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
fake = Faker()

# ---------------- DB CONFIG ----------------
conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", "12345"),
    database=os.getenv("MYSQL_DATABASE", "retail_inventory")
)
cursor = conn.cursor()

# ---------------- PARAMETERS ----------------
NUM_STORES = 50
NUM_SUPPLIERS = 100
NUM_PRODUCTS = 500
NUM_INVENTORY = 5000

# ---------------- STORES ----------------
stores = []
for _ in range(NUM_STORES):
    stores.append((
        fake.company(),
        fake.city(),
        fake.state(),
        fake.zipcode()
    ))
cursor.executemany("INSERT INTO stores (store_name, city, state, zipcode) VALUES (%s,%s,%s,%s)", stores)
conn.commit()

cursor.execute("SELECT store_id FROM stores")
store_ids = [row[0] for row in cursor.fetchall()]

# ---------------- SUPPLIERS ----------------
suppliers = []
for _ in range(NUM_SUPPLIERS):
    suppliers.append((
        fake.company() + " Supplier",
        fake.phone_number(),
        fake.email()
    ))
cursor.executemany("INSERT INTO suppliers (supplier_name, contact_phone, contact_email) VALUES (%s,%s,%s)", suppliers)
conn.commit()

cursor.execute("SELECT supplier_id FROM suppliers")
supplier_ids = [row[0] for row in cursor.fetchall()]

# ---------------- PRODUCTS ----------------
products = []
CATEGORIES = ['Electronics', 'Clothing', 'Food', 'Furniture', 'Toys', 'Home Appliances']
for _ in range(NUM_PRODUCTS):
    products.append((
        fake.word().capitalize(),
        random.choice(CATEGORIES),
        random.choice(supplier_ids),
        round(random.uniform(5.0, 500.0), 2)
    ))
cursor.executemany("INSERT INTO products (product_name, category, supplier_id, price) VALUES (%s,%s,%s,%s)", products)
conn.commit()

cursor.execute("SELECT product_id FROM products")
product_ids = [row[0] for row in cursor.fetchall()]

# ---------------- INVENTORY ----------------
inventory = []
for _ in range(NUM_INVENTORY):
    inventory.append((
        random.choice(store_ids),
        random.choice(product_ids),
        random.randint(10, 1000),
        fake.date_this_year()
    ))
cursor.executemany("INSERT INTO inventory (store_id, product_id, stock_level, last_restock_date) VALUES (%s,%s,%s,%s)", inventory)
conn.commit()

print("✅ Retail Inventory records generated successfully")
cursor.close()
conn.close()