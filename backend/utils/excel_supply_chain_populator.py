import os
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker


fake = Faker()
ROWS = int(os.getenv("EXCEL_SUPPLY_ROWS", "2000"))
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.getenv("EXCEL_SUPPLY_FILE", "excel_supply_chain_demo.xlsx")

WAREHOUSES = ["WH-N1", "WH-S1", "WH-E1", "WH-W1", "WH-C1"]
TRANSPORT = ["Road", "Rail", "Air", "Sea"]


def build_dataframe(rows: int) -> pd.DataFrame:
    records = []
    for i in range(1, rows + 1):
        ordered = date.today() - timedelta(days=random.randint(0, 365))
        lead_days = random.randint(1, 25)
        delivered = ordered + timedelta(days=lead_days)

        records.append(
            {
                "movement_id": i,
                "po_number": f"PO-{random.randint(10000, 99999)}",
                "warehouse": random.choice(WAREHOUSES),
                "supplier": fake.company(),
                "ordered_date": ordered,
                "delivered_date": delivered,
                "transport_mode": random.choice(TRANSPORT),
                "lead_time_days": lead_days,
                "units_received": random.randint(10, 4000),
                "defect_rate": round(random.uniform(0.0, 0.08), 4),
                "shipping_cost": round(random.uniform(400, 85000), 2),
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
