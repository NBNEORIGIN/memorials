from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Memorial Types ──
class MemorialTypeOut(BaseModel):
    id: int
    name: str
    dimensions_mm: Optional[dict] = None
    sort_order: int
    is_active: bool
    model_config = {"from_attributes": True}


class MemorialTypeCreate(BaseModel):
    name: str
    dimensions_mm: Optional[dict] = None
    sort_order: int = 0


# ── Colours ──
class ColourOut(BaseModel):
    id: int
    name: str
    hex_code: Optional[str] = None
    is_bw: bool
    model_config = {"from_attributes": True}


class ColourCreate(BaseModel):
    name: str
    hex_code: Optional[str] = None
    is_bw: bool = False


# ── Decoration Types ──
class DecorationTypeOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


# ── Themes ──
class ThemeOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


# ── Processors ──
class ProcessorOut(BaseModel):
    id: int
    key: str
    display_name: str
    description: Optional[str] = None
    is_active: bool
    model_config = {"from_attributes": True}


# ── SKU Mappings ──
class SkuMappingOut(BaseModel):
    id: int
    sku: str
    colour: ColourOut
    memorial_type: MemorialTypeOut
    decoration_type: Optional[DecorationTypeOut] = None
    theme: Optional[ThemeOut] = None
    processor: ProcessorOut
    model_config = {"from_attributes": True}


class SkuMappingCreate(BaseModel):
    sku: str
    colour_id: int
    memorial_type_id: int
    decoration_type_id: Optional[int] = None
    theme_id: Optional[int] = None
    processor_id: int


# ── Job Items ──
class JobItemOut(BaseModel):
    id: int
    order_id: Optional[str] = None
    order_item_id: Optional[str] = None
    sku: str
    quantity: int
    colour: Optional[str] = None
    memorial_type: Optional[str] = None
    decoration_type: Optional[str] = None
    theme: Optional[str] = None
    processor_key: Optional[str] = None
    graphic: Optional[str] = None
    line_1: Optional[str] = None
    line_2: Optional[str] = None
    line_3: Optional[str] = None
    image_path: Optional[str] = None
    svg_path: Optional[str] = None
    status: str
    error: Optional[str] = None
    model_config = {"from_attributes": True}


class JobItemUpdate(BaseModel):
    graphic: Optional[str] = None
    line_1: Optional[str] = None
    line_2: Optional[str] = None
    line_3: Optional[str] = None


# ── Jobs ──
class JobOut(BaseModel):
    id: int
    source: str
    status: str
    filename: Optional[str] = None
    item_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    items: list[JobItemOut] = []
    model_config = {"from_attributes": True}


class JobSummaryOut(BaseModel):
    id: int
    source: str
    status: str
    filename: Optional[str] = None
    item_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
