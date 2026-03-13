"""CRUD endpoints for SKU mappings and reference data (colours, types, themes, processors)."""

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import (
    SkuMapping, MemorialType, Colour, DecorationType, Theme, Processor,
)
from app.schemas import (
    SkuMappingOut, SkuMappingCreate,
    MemorialTypeOut, MemorialTypeCreate,
    ColourOut, ColourCreate,
    DecorationTypeOut, ThemeOut, ProcessorOut,
)

router = APIRouter(prefix="/api/skus", tags=["SKU Management"])


# ── Reference data ──

@router.get("/memorial-types", response_model=list[MemorialTypeOut])
def list_memorial_types(db: Session = Depends(get_db)):
    return db.query(MemorialType).filter(MemorialType.is_active).order_by(MemorialType.sort_order).all()


@router.post("/memorial-types", response_model=MemorialTypeOut, status_code=201)
def create_memorial_type(data: MemorialTypeCreate, db: Session = Depends(get_db)):
    obj = MemorialType(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/colours", response_model=list[ColourOut])
def list_colours(db: Session = Depends(get_db)):
    return db.query(Colour).order_by(Colour.name).all()


@router.post("/colours", response_model=ColourOut, status_code=201)
def create_colour(data: ColourCreate, db: Session = Depends(get_db)):
    obj = Colour(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/decoration-types", response_model=list[DecorationTypeOut])
def list_decoration_types(db: Session = Depends(get_db)):
    return db.query(DecorationType).order_by(DecorationType.name).all()


@router.get("/themes", response_model=list[ThemeOut])
def list_themes(db: Session = Depends(get_db)):
    return db.query(Theme).order_by(Theme.name).all()


@router.get("/processors", response_model=list[ProcessorOut])
def list_processors(db: Session = Depends(get_db)):
    return db.query(Processor).filter(Processor.is_active).order_by(Processor.display_name).all()


# ── SKU Mappings ──

@router.get("/", response_model=list[SkuMappingOut])
def list_sku_mappings(db: Session = Depends(get_db)):
    return (
        db.query(SkuMapping)
        .options(
            joinedload(SkuMapping.colour),
            joinedload(SkuMapping.memorial_type),
            joinedload(SkuMapping.decoration_type),
            joinedload(SkuMapping.theme),
            joinedload(SkuMapping.processor),
        )
        .order_by(SkuMapping.sku)
        .all()
    )


@router.get("/{sku}", response_model=SkuMappingOut)
def get_sku_mapping(sku: str, db: Session = Depends(get_db)):
    mapping = (
        db.query(SkuMapping)
        .options(
            joinedload(SkuMapping.colour),
            joinedload(SkuMapping.memorial_type),
            joinedload(SkuMapping.decoration_type),
            joinedload(SkuMapping.theme),
            joinedload(SkuMapping.processor),
        )
        .filter(SkuMapping.sku == sku)
        .first()
    )
    if not mapping:
        raise HTTPException(status_code=404, detail=f"SKU '{sku}' not found")
    return mapping


@router.post("/", response_model=SkuMappingOut, status_code=201)
def create_sku_mapping(data: SkuMappingCreate, db: Session = Depends(get_db)):
    existing = db.query(SkuMapping).filter_by(sku=data.sku).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"SKU '{data.sku}' already exists")
    obj = SkuMapping(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return get_sku_mapping(obj.sku, db)


@router.put("/{mapping_id}", response_model=SkuMappingOut)
def update_sku_mapping(mapping_id: int, data: SkuMappingCreate, db: Session = Depends(get_db)):
    obj = db.query(SkuMapping).get(mapping_id)
    if not obj:
        raise HTTPException(status_code=404, detail="SKU mapping not found")
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return get_sku_mapping(obj.sku, db)


@router.delete("/{mapping_id}", status_code=204)
def delete_sku_mapping(mapping_id: int, db: Session = Depends(get_db)):
    obj = db.query(SkuMapping).get(mapping_id)
    if not obj:
        raise HTTPException(status_code=404, detail="SKU mapping not found")
    db.delete(obj)
    db.commit()


@router.post("/import-csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Bulk import SKU mappings from a CSV file.

    Expected columns: SKU, COLOUR, TYPE, DecorationType, Theme, ProcessorCategory
    Matches existing reference data by name; creates new entries if missing.
    Skips rows where SKU already exists.
    """
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        sku = (row.get("SKU") or "").strip()
        if not sku:
            continue

        colour_name = (row.get("COLOUR") or "").strip().title()
        type_name = (row.get("TYPE") or "").strip()
        proc_key = (row.get("ProcessorCategory") or "").strip()
        deco_name = (row.get("DecorationType") or "").strip()
        theme_name = (row.get("Theme") or "").strip()

        if not colour_name or not type_name:
            errors.append(f"Row {i}: missing colour or type for SKU '{sku}'")
            continue

        # Check if already exists
        if db.query(SkuMapping).filter_by(sku=sku).first():
            skipped += 1
            continue

        # Resolve colour
        colour = db.query(Colour).filter_by(name=colour_name).first()
        if not colour:
            colour = Colour(name=colour_name)
            db.add(colour)
            db.flush()

        # Resolve type
        mem_type = db.query(MemorialType).filter_by(name=type_name).first()
        if not mem_type:
            mem_type = MemorialType(name=type_name)
            db.add(mem_type)
            db.flush()

        # Resolve processor
        if not proc_key:
            proc_key = "unclassified"
        processor = db.query(Processor).filter_by(key=proc_key).first()
        if not processor:
            processor = Processor(key=proc_key, display_name=proc_key.replace("_", " ").title())
            db.add(processor)
            db.flush()

        # Resolve optional decoration type
        deco = None
        if deco_name:
            deco = db.query(DecorationType).filter_by(name=deco_name).first()
            if not deco:
                deco = DecorationType(name=deco_name)
                db.add(deco)
                db.flush()

        # Resolve optional theme
        theme = None
        if theme_name:
            theme = db.query(Theme).filter_by(name=theme_name).first()
            if not theme:
                theme = Theme(name=theme_name)
                db.add(theme)
                db.flush()

        mapping = SkuMapping(
            sku=sku,
            colour_id=colour.id,
            memorial_type_id=mem_type.id,
            processor_id=processor.id,
            decoration_type_id=deco.id if deco else None,
            theme_id=theme.id if theme else None,
        )
        db.add(mapping)
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}
