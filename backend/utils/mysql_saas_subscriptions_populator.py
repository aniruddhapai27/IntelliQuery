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
    database=os.getenv("MYSQL_DATABASE", "saas_subscriptions")
)
cursor = conn.cursor()

# ---------------- PARAMETERS ----------------
NUM_USERS = 2000
NUM_SUBSCRIPTIONS = 2500
NUM_PAYMENTS = 10000

# ---------------- PLANS ----------------
plans = [
    ("Basic", 9.99, "monthly"),
    ("Pro", 29.99, "monthly"),
    ("Enterprise", 99.99, "monthly"),
    ("Yearly Pro", 299.99, "yearly")
]
cursor.executemany("INSERT INTO plans (plan_name, price, billing_cycle) VALUES (%s,%s,%s)", plans)
conn.commit()

cursor.execute("SELECT plan_id FROM plans")
plan_ids = [row[0] for row in cursor.fetchall()]

# ---------------- USERS ----------------
users = [(fake.name(), fake.email(), fake.date_between(start_date="-3y", end_date="today")) for _ in range(NUM_USERS)]
cursor.executemany("INSERT INTO users (name, email, signup_date) VALUES (%s,%s,%s)", users)
conn.commit()

cursor.execute("SELECT user_id FROM users")
user_ids = [row[0] for row in cursor.fetchall()]

# ---------------- SUBSCRIPTIONS ----------------
subs = []
STATUSES = ["ACTIVE", "CANCELED", "PAST_DUE"]
for _ in range(NUM_SUBSCRIPTIONS):
    subs.append((
        random.choice(user_ids),
        random.choice(plan_ids),
        fake.date_between(start_date="-2y", end_date="today"),
        random.choice(STATUSES)
    ))
cursor.executemany("INSERT INTO subscriptions (user_id, plan_id, start_date, status) VALUES (%s,%s,%s,%s)", subs)
conn.commit()

cursor.execute("SELECT subscription_id FROM subscriptions")
sub_ids = [row[0] for row in cursor.fetchall()]

# ---------------- PAYMENTS ----------------
paymts = []
for _ in range(NUM_PAYMENTS):
    paymts.append((
        random.choice(sub_ids),
        round(random.uniform(9.99, 100.0), 2),
        fake.date_between(start_date="-1y", end_date="today"),
        "SUCCESS"
    ))
cursor.executemany("INSERT INTO payments (subscription_id, amount, payment_date, status) VALUES (%s,%s,%s,%s)", paymts)
conn.commit()

print("✅ SaaS Subscriptions records generated successfully")
cursor.close()
conn.close()