"""Seed production database from seed_data.json export."""
import json
import sqlite3
import sys
import os

DB_PATH = os.environ.get("DB_PATH", "./data/memorials.db")

with open("seed_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Insert order matters due to foreign keys
INSERT_ORDER = ["colours", "memorial_types", "decoration_types", "themes", "processors", "sku_mappings"]

for table in INSERT_ORDER:
    rows = data.get(table, [])
    if not rows:
        continue

    cols = list(rows[0].keys())
    placeholders = ", ".join(["?"] * len(cols))
    col_names = ", ".join(cols)

    # Clear existing data
    cur.execute(f"DELETE FROM {table}")

    for row in rows:
        values = [row[c] for c in cols]
        cur.execute(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", values)

    print(f"{table}: {len(rows)} rows inserted")

conn.commit()
conn.close()
print("\nSeed complete!")
