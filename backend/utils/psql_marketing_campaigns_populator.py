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
    database=os.getenv("POSTGRES_DATABASE", "marketing_campaigns"),
    port=os.getenv("POSTGRES_PORT", "5432")
)
cursor = conn.cursor()

# ---------------- PARAMETERS ----------------
NUM_CHANNELS = 5
NUM_CAMPAIGNS = 50
NUM_LEADS = 3000
NUM_ENGAGEMENTS = 10000

# ---------------- CHANNELS ----------------
channels = [
    ("Email", "Email marketing platform"),
    ("Social Media", "Social networks"),
    ("Search Ads", "Search engine marketing"),
    ("Affiliate", "Affiliate partners"),
    ("Direct", "Direct traffic")
]
cursor.executemany("INSERT INTO channels (channel_name, description) VALUES (%s,%s)", channels)
conn.commit()

cursor.execute("SELECT channel_id FROM channels")
channel_ids = [row[0] for row in cursor.fetchall()]

# ---------------- CAMPAIGNS ----------------
campaigns = []
STATUSES = ["ACTIVE", "PAUSED", "COMPLETED"]
for _ in range(NUM_CAMPAIGNS):
    campaigns.append((
        fake.catch_phrase() + " Campaign",
        random.choice(channel_ids),
        round(random.uniform(500, 10000), 2),
        fake.date_between(start_date="-1y", end_date="today"),
        random.choice(STATUSES)
    ))
cursor.executemany("INSERT INTO campaigns (campaign_name, channel_id, budget, start_date, status) VALUES (%s,%s,%s,%s,%s)", campaigns)
conn.commit()

cursor.execute("SELECT campaign_id FROM campaigns")
campaign_ids = [row[0] for row in cursor.fetchall()]

# ---------------- LEADS ----------------
leads = []
for _ in range(NUM_LEADS):
    leads.append((
        fake.name(),
        fake.email(),
        fake.company(),
        random.choice(campaign_ids)
    ))
cursor.executemany("INSERT INTO leads (name, email, company, source_campaign_id) VALUES (%s,%s,%s,%s)", leads)
conn.commit()

cursor.execute("SELECT lead_id FROM leads")
lead_ids = [row[0] for row in cursor.fetchall()]

# ---------------- ENGAGEMENTS ----------------
engagements = []
TYPES = ["CLICK", "OPEN", "REPLY", "PURCHASE", "UNSUBSCRIBE"]
for _ in range(NUM_ENGAGEMENTS):
    engagements.append((
        random.choice(lead_ids),
        random.choice(campaign_ids),
        random.choice(TYPES),
        fake.date_time_between(start_date="-1y", end_date="now")
    ))
cursor.executemany("INSERT INTO engagements (lead_id, campaign_id, engagement_type, event_time) VALUES (%s,%s,%s,%s)", engagements)
conn.commit()

print("✅ Marketing Campaigns records generated successfully")
cursor.close()
conn.close()