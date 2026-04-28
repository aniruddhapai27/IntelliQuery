import os
import random
from datetime import datetime, timedelta

from faker import Faker
from pymongo import MongoClient


fake = Faker()
ROWS = int(os.getenv("MONGO_EVENT_ROWS", "3500"))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "intelliquery_demo")
COLLECTION = os.getenv("MONGO_EVENT_COLLECTION", "event_analytics")

EVENTS = ["page_view", "signup", "login", "search", "checkout", "logout"]
PLATFORMS = ["web", "android", "ios"]


def generate_documents(rows: int) -> list[dict]:
    docs = []
    for i in range(1, rows + 1):
        docs.append(
            {
                "event_id": f"EVT-{i:07d}",
                "event_name": random.choice(EVENTS),
                "event_ts": datetime.utcnow() - timedelta(minutes=random.randint(0, 800000)),
                "user_id": random.randint(1000, 60000),
                "session_id": f"SES-{random.randint(1, 999999):06d}",
                "platform": random.choice(PLATFORMS),
                "country": fake.country(),
                "properties": {
                    "duration_sec": random.randint(2, 1800),
                    "is_new_user": random.random() < 0.2,
                    "screen": fake.word(),
                },
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
    collection.create_index("event_ts")
    collection.create_index("event_name")
    collection.create_index("user_id")

    print(f"Inserted {len(result.inserted_ids)} docs into MongoDB collection '{COLLECTION}'.")


if __name__ == "__main__":
    populate()
