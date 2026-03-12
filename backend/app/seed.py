"""Seed the database with memorial types, colours, themes, processors, and SKU mappings
from the existing SKULIST.csv data."""

import csv
import os
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, Base
from app.models import MemorialType, Colour, DecorationType, Theme, Processor, SkuMapping


# ── Colour metadata ──
COLOUR_META = {
    "Copper":    {"hex_code": "#B87333", "is_bw": False},
    "Gold":      {"hex_code": "#FFD700", "is_bw": False},
    "Silver":    {"hex_code": "#C0C0C0", "is_bw": False},
    "Stone":     {"hex_code": "#8B8680", "is_bw": False},
    "Marble":    {"hex_code": "#E8E0D8", "is_bw": False},
    "Black":     {"hex_code": "#1a1a1a", "is_bw": True},
    "Slate":     {"hex_code": "#708090", "is_bw": True},
    "Brass":     {"hex_code": "#B5A642", "is_bw": False},
    "Aluminium": {"hex_code": "#A8A9AD", "is_bw": False},
}

# ── Memorial type dimensions (mm) ──
TYPE_DIMENSIONS = {
    "Regular Stake":  {"width": 140, "height": 90},
    "Large Stake":    {"width": 200, "height": 120},
    "Small Stake":    {"width": 100, "height": 60},
    "Heart Stake":    {"width": 140, "height": 140},
    "Regular Plaque": {"width": 140, "height": 90},
    "Large Metal":    {"width": 200, "height": 120},
    "Medium Metal":   {"width": 160, "height": 100},
    "Small Metal":    {"width": 120, "height": 80},
    "XL Metal":       {"width": 250, "height": 150},
}

# ── Processor display names ──
PROCESSOR_DISPLAY = {
    "regular_stakes_graphic_coloured": "Regular Stake — Coloured Graphic",
    "regular_stakes_graphic_bw":       "Regular Stake — B&W Graphic",
    "regular_stakes_photo_coloured":   "Regular Stake — Coloured Photo",
    "regular_stakes_photo_bw":         "Regular Stake — B&W Photo",
    "large_stakes_graphic_coloured":   "Large Stake — Coloured Graphic",
    "large_stakes_graphic_bw":         "Large Stake — B&W Graphic",
    "large_stakes_photo_coloured":     "Large Stake — Coloured Photo",
    "large_stakes_photo_bw":           "Large Stake — B&W Photo",
    "small_stakes_graphic_coloured":   "Small Stake — Coloured Graphic",
    "small_stakes_graphic_bw":         "Small Stake — B&W Graphic",
    "heart_stakes_graphic_coloured":   "Heart Stake — Coloured Graphic",
    "heart_stakes_graphic":            "Heart Stake — Graphic",
    "large_metal_graphic":             "Large Metal — Graphic",
    "medium_metal_graphic":            "Medium Metal — Graphic",
    "small_metal_graphic":             "Small Metal — Graphic",
    "xl_metal_graphic":                "XL Metal — Graphic",
    "unclassified":                    "Unclassified",
}


def get_or_create(db: Session, model, defaults=None, **kwargs):
    """Get existing record or create new one."""
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance, True


def seed_from_skulist(db: Session, skulist_path: str):
    """Parse SKULIST.csv and populate all reference tables + SKU mappings."""
    created_counts = {
        "memorial_types": 0, "colours": 0, "decoration_types": 0,
        "themes": 0, "processors": 0, "sku_mappings": 0,
    }

    with open(skulist_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        sku = row.get("SKU", "").strip()
        if not sku:
            continue

        colour_name = row.get("COLOUR", "").strip()
        type_name = row.get("TYPE", "").strip()
        deco_name = row.get("DecorationType", "").strip()
        theme_name = row.get("Theme", "").strip()
        proc_key = row.get("ProcessorCategory", "").strip()

        if not colour_name or not type_name:
            print(f"  SKIP {sku}: missing colour or type")
            continue

        # Normalise colour name to title case
        colour_name = colour_name.strip().title()

        # Memorial type
        dims = TYPE_DIMENSIONS.get(type_name)
        mem_type, created = get_or_create(db, MemorialType, name=type_name,
                                          defaults={"dimensions_mm": dims})
        if created:
            created_counts["memorial_types"] += 1

        # Colour
        meta = COLOUR_META.get(colour_name, {"hex_code": None, "is_bw": False})
        colour, created = get_or_create(db, Colour, name=colour_name, defaults=meta)
        if created:
            created_counts["colours"] += 1

        # Decoration type (optional)
        deco = None
        if deco_name:
            deco, created = get_or_create(db, DecorationType, name=deco_name)
            if created:
                created_counts["decoration_types"] += 1

        # Theme (optional)
        theme = None
        if theme_name:
            theme, created = get_or_create(db, Theme, name=theme_name)
            if created:
                created_counts["themes"] += 1

        # Processor
        if not proc_key:
            proc_key = "unclassified"
        display = PROCESSOR_DISPLAY.get(proc_key, proc_key.replace("_", " ").title())
        processor, created = get_or_create(db, Processor, key=proc_key,
                                           defaults={"display_name": display})
        if created:
            created_counts["processors"] += 1

        # SKU mapping (skip duplicates)
        existing = db.query(SkuMapping).filter_by(sku=sku).first()
        if existing:
            continue

        mapping = SkuMapping(
            sku=sku,
            colour_id=colour.id,
            memorial_type_id=mem_type.id,
            decoration_type_id=deco.id if deco else None,
            theme_id=theme.id if theme else None,
            processor_id=processor.id,
        )
        db.add(mapping)
        created_counts["sku_mappings"] += 1

    db.commit()
    return created_counts


def run_seed():
    """Create tables and seed from SKULIST.csv."""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    # Look for SKULIST.csv in several locations
    candidates = [
        Path(__file__).parent.parent / "assets" / "SKULIST.csv",
        Path(r"D:\Google Drive\My Drive\003 APPS\AmazonPhotoProcessor 2\assets\SKULIST.csv"),
        Path(r"D:\Google Drive\My Drive\003 APPS\AmazonSeller -CURRENT VERSION\assets\SKULIST.csv"),
    ]
    skulist_path = None
    for p in candidates:
        if p.exists():
            skulist_path = str(p)
            break

    if not skulist_path:
        print("ERROR: SKULIST.csv not found. Checked:")
        for p in candidates:
            print(f"  {p}")
        return

    print(f"Seeding from: {skulist_path}")
    db = SessionLocal()
    try:
        counts = seed_from_skulist(db, skulist_path)
        print("Seed complete:")
        for table, count in counts.items():
            print(f"  {table}: {count} created")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
