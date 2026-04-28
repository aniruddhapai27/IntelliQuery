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
    database=os.getenv("POSTGRES_DATABASE", "logistics_shipments"),
    port=os.getenv("POSTGRES_PORT", "5432")
)
cursor = conn.cursor()

# ---------------- PARAMETERS ----------------
NUM_WAREHOUSES = 20
NUM_VEHICLES = 100
NUM_ROUTES = 500
NUM_SHIPMENTS = 5000

# ---------------- WAREHOUSES ----------------
warehouses = []
for _ in range(NUM_WAREHOUSES):
    warehouses.append((
        fake.city() + " Hub",
        fake.address(),
        random.randint(10000, 50000)
    ))
cursor.executemany("INSERT INTO warehouses (warehouse_name, location, capacity) VALUES (%s,%s,%s)", warehouses)
conn.commit()

cursor.execute("SELECT warehouse_id FROM warehouses")
warehouse_ids = [row[0] for row in cursor.fetchall()]

# ---------------- VEHICLES ----------------
vehicles = []
TYPES = ["Truck", "Van", "Lorry", "Freighter"]
for _ in range(NUM_VEHICLES):
    vehicles.append((
        fake.license_plate(),
        random.choice(TYPES),
        round(random.uniform(1000.0, 5000.0), 2)
    ))
cursor.executemany("INSERT INTO vehicles (license_plate, vehicle_type, max_load) VALUES (%s,%s,%s)", vehicles)
conn.commit()

cursor.execute("SELECT vehicle_id FROM vehicles")
vehicle_ids = [row[0] for row in cursor.fetchall()]

# ---------------- ROUTES ----------------
routes = []
for _ in range(NUM_ROUTES):
    routes.append((
        fake.city(),
        fake.city(),
        round(random.uniform(50.0, 1500.0), 2)
    ))
cursor.executemany("INSERT INTO routes (origin, destination, distance_km) VALUES (%s,%s,%s)", routes)
conn.commit()

cursor.execute("SELECT route_id FROM routes")
route_ids = [row[0] for row in cursor.fetchall()]

# ---------------- SHIPMENTS ----------------
shipments = []
STATUSES = ["PENDING", "IN_TRANSIT", "DELIVERED", "FAILED"]
for _ in range(NUM_SHIPMENTS):
    shipments.append((
        random.choice(warehouse_ids),
        random.choice(vehicle_ids),
        random.choice(route_ids),
        fake.date_between(start_date="-1y", end_date="today"),
        random.choice(STATUSES)
    ))
cursor.executemany("INSERT INTO shipments (warehouse_id, vehicle_id, route_id, shipment_date, status) VALUES (%s,%s,%s,%s,%s)", shipments)
conn.commit()

print("✅ Logistics Shipments records generated successfully")
cursor.close()
conn.close()