import os
import random

from faker import Faker
from pymongo import MongoClient


fake = Faker()
ROWS = int(os.getenv("MONGO_CATALOG_ROWS", "1800"))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "intelliquery_demo")
COLLECTION = os.getenv("MONGO_CATALOG_COLLECTION", "product_catalog")

CATEGORIES = ["Electronics", "Fashion", "Home", "Books", "Sports"]
BRANDS = ["Aster", "Nova", "Lume", "Terra", "Axis"]


def generate_documents(rows: int) -> list[dict]:
    docs = []
    for i in range(1, rows + 1):
        variants = []
        for _ in range(random.randint(1, 4)):
            variants.append(
                {
                    "sku": f"SKU-{random.randint(100000, 999999)}",
                    "color": random.choice(["Black", "White", "Blue", "Red", "Green"]),
                    "size": random.choice(["S", "M", "L", "XL", "NA"]),
                    "stock": random.randint(0, 500),
                }
            )

        docs.append(
            {
                "product_id": f"PRD-{i:06d}",
                "name": f"{fake.word().title()} {fake.word().title()}",
                "brand": random.choice(BRANDS),
                "category": random.choice(CATEGORIES),
                "price": round(random.uniform(9, 2500), 2),
                "rating": round(random.uniform(2.5, 5.0), 1),
                "tags": random.sample(["new", "popular", "discount", "premium", "eco"], k=2),
                "variants": variants,
                "active": random.random() > 0.07,
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
    collection.create_index("category")
    collection.create_index("brand")
    collection.create_index("price")

    print(f"Inserted {len(result.inserted_ids)} docs into MongoDB collection '{COLLECTION}'.")


if __name__ == "__main__":
    populate()
