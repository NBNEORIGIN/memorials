"""CRUD endpoints for SKU mappings and reference data (colours, types, themes, processors)."""

from fastapi import APIRouter, Depends, HTTPException
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
