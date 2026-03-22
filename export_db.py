"""Export all reference data from local SQLite to JSON for seeding production."""
import sqlite3
import json

conn = sqlite3.connect("backend/memorials.db")
conn.row_factory = sqlite3.Row

tables = ["colours", "memorial_types", "decoration_types", "themes", "processors", "sku_mappings"]
data = {}

for table in tables:
    try:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        data[table] = [dict(r) for r in rows]
        print(f"{table}: {len(rows)} rows")
    except Exception as e:
        print(f"{table}: ERROR - {e}")

conn.close()

with open("seed_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, default=str)

print(f"\nExported to seed_data.json")
