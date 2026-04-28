import os
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker


fake = Faker()
ROWS = int(os.getenv("EXCEL_SALES_ROWS", "2500"))
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.getenv("EXCEL_SALES_FILE", "excel_sales_kpi_demo.xlsx")

REGIONS = ["North", "South", "East", "West", "Central"]
CHANNELS = ["Online", "Retail", "Partner"]


def build_dataframe(rows: int) -> pd.DataFrame:
    records = []
    for i in range(1, rows + 1):
        revenue = round(random.uniform(100, 15000), 2)
        returns = round(revenue * random.uniform(0.0, 0.12), 2)
        net = round(revenue - returns, 2)

        records.append(
            {
                "record_id": i,
                "sale_date": date.today() - timedelta(days=random.randint(0, 365)),
                "region": random.choice(REGIONS),
                "channel": random.choice(CHANNELS),
                "sales_rep": fake.name(),
                "units_sold": random.randint(1, 40),
                "gross_revenue": revenue,
                "returns_amount": returns,
                "net_revenue": net,
                "customer_satisfaction": round(random.uniform(3.0, 5.0), 2),
            }
        )
    return pd.DataFrame(records)


def populate() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    df = build_dataframe(ROWS)
    df.to_excel(output_path, index=False)
    print(f"Saved {len(df)} rows to Excel file '{output_path}'.")


if __name__ == "__main__":
    populate()
