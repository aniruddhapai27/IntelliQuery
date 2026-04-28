import os
import random
from datetime import datetime, timedelta

from faker import Faker
from pymongo import MongoClient


fake = Faker()
ROWS = int(os.getenv("MONGO_TICKET_ROWS", "2200"))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "intelliquery_demo")
COLLECTION = os.getenv("MONGO_TICKET_COLLECTION", "support_tickets")

PRIORITIES = ["Low", "Medium", "High", "Critical"]
STATUS = ["Open", "InProgress", "Resolved", "Closed"]
CHANNELS = ["Email", "Chat", "Phone", "WebForm"]


def generate_documents(rows: int) -> list[dict]:
    docs = []
    for i in range(1, rows + 1):
        created_at = datetime.utcnow() - timedelta(days=random.randint(0, 365))
        resolved = random.random() < 0.72
        resolved_at = created_at + timedelta(hours=random.randint(2, 168)) if resolved else None

        docs.append(
            {
                "ticket_id": f"TIC-{i:07d}",
                "customer_id": random.randint(10000, 99999),
                "created_at": created_at,
                "resolved_at": resolved_at,
                "priority": random.choices(PRIORITIES, weights=[35, 40, 20, 5])[0],
                "status": random.choices(STATUS, weights=[10, 18, 47, 25])[0],
                "channel": random.choice(CHANNELS),
                "category": random.choice(["Billing", "Technical", "Onboarding", "Account"]),
                "sentiment": random.choice(["Positive", "Neutral", "Negative"]),
                "agent_notes": [fake.sentence() for _ in range(random.randint(1, 3))],
            }
        )
    return docs


def populate() -> None:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    db.command("ping")
    collection = db[COLLECTION]
    collection.drop()

    docs = generate_documents(ROWS)
    result = collection.insert_many(docs)
    collection.create_index("created_at")
    collection.create_index("priority")
    collection.create_index("status")

    print(f"Inserted {len(result.inserted_ids)} docs into MongoDB collection '{COLLECTION}'.")


if __name__ == "__main__":
    populate()
