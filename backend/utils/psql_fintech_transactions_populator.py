import os
from faker import Faker
import random
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
fake = Faker()

# ---------------- DB CONFIG ----------------
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "12345"),
    database=os.getenv("POSTGRES_DATABASE", "fintech_transactions"),
    port=os.getenv("POSTGRES_PORT", "5432")
)
cursor = conn.cursor()

# ---------------- PARAMETERS ----------------
NUM_USERS = 3000
NUM_ACCOUNTS = 4000
NUM_TRANSACTIONS = 15000

# ---------------- USERS ----------------
usrs = [(fake.name(), fake.email(), fake.date_between("-5y", "today")) for _ in range(NUM_USERS)]
cursor.executemany("INSERT INTO users (name, email, joined_date) VALUES (%s,%s,%s)", usrs)
conn.commit()

cursor.execute("SELECT user_id FROM users")
user_ids = [row[0] for row in cursor.fetchall()]

# ---------------- ACCOUNTS ----------------
accs = []
TYPES = ["CHECKING", "SAVINGS", "CREDIT"]
for _ in range(NUM_ACCOUNTS):
    accs.append((
        random.choice(user_ids),
        random.choice(TYPES),
        round(random.uniform(100, 50000), 2)
    ))
cursor.executemany("INSERT INTO accounts (user_id, account_type, balance) VALUES (%s,%s,%s)", accs)
conn.commit()

cursor.execute("SELECT account_id FROM accounts")
acc_ids = [row[0] for row in cursor.fetchall()]

# ---------------- TRANSACTIONS ----------------
txns = []
TXN_TYPES = ["DEPOSIT", "WITHDRAWAL", "TRANSFER"]
for _ in range(NUM_TRANSACTIONS):
    txns.append((
        random.choice(acc_ids),
        random.choice(TXN_TYPES),
        round(random.uniform(5, 2000), 2),
        fake.date_time_between("-1y", "now")
    ))
cursor.executemany("INSERT INTO transactions (account_id, transaction_type, amount, transaction_date) VALUES (%s,%s,%s,%s)", txns)
conn.commit()

print("✅ Fintech Transactions records generated successfully")
cursor.close()
conn.close()