import os
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker


fake = Faker()
ROWS = int(os.getenv("EXCEL_HR_ROWS", "1800"))
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.getenv("EXCEL_HR_FILE", "excel_hr_attrition_demo.xlsx")

DEPARTMENTS = ["Engineering", "Sales", "Support", "HR", "Finance", "Marketing"]
WORK_MODES = ["Remote", "Hybrid", "Onsite"]


def build_dataframe(rows: int) -> pd.DataFrame:
    records = []
    for i in range(1, rows + 1):
        tenure_months = random.randint(1, 120)
        perf = round(random.uniform(2.0, 5.0), 2)
        attrition = random.random() < 0.14

        records.append(
            {
                "employee_row_id": i,
                "employee_id": f"EMP-{i:06d}",
                "department": random.choice(DEPARTMENTS),
                "job_level": random.randint(1, 7),
                "work_mode": random.choice(WORK_MODES),
                "monthly_salary": random.randint(25000, 350000),
                "tenure_months": tenure_months,
                "last_promotion_date": date.today() - timedelta(days=random.randint(30, 1200)),
                "performance_score": perf,
                "attrition_risk_score": round(random.uniform(0.02, 0.98), 3),
                "is_attrited": attrition,
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
