"""Cell layout CRUD + live preview endpoint for the Layout Teaching Tool."""

import io
import os
from typing import Optional

import svgwrite
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import CellLayout
from app.schemas import CellLayoutOut, CellLayoutCreate, CellLayoutUpdate
from app.processors.base import PX_PER_MM, PT_TO_MM, embed_image, split_line_to_fit
from app.processors.registry import get_processor, _REGISTRY

router = APIRouter(prefix="/api/layouts", tags=["Cell Layouts"])


# ── CRUD ──────────────────────────────────────────────────────────

@router.get("/", response_model=list[CellLayoutOut])
def list_layouts(db: Session = Depends(get_db)):
    return db.query(CellLayout).order_by(CellLayout.processor_key).all()


@router.get("/{processor_key}", response_model=CellLayoutOut)
def get_layout(processor_key: str, db: Session = Depends(get_db)):
    layout = db.query(CellLayout).filter(CellLayout.processor_key == processor_key).first()
    if not layout:
        raise HTTPException(status_code=404, detail=f"No layout for '{processor_key}'")
    return layout


@router.post("/", response_model=CellLayoutOut, status_code=201)
def create_layout(data: CellLayoutCreate, db: Session = Depends(get_db)):
    existing = db.query(CellLayout).filter(CellLayout.processor_key == data.processor_key).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Layout for '{data.processor_key}' already exists")
    obj = CellLayout(**data.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{processor_key}", response_model=CellLayoutOut)
def update_layout(processor_key: str, data: CellLayoutUpdate, db: Session = Depends(get_db)):
    obj = db.query(CellLayout).filter(CellLayout.processor_key == processor_key).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"No layout for '{processor_key}'")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{processor_key}", status_code=204)
def delete_layout(processor_key: str, db: Session = Depends(get_db)):
    obj = db.query(CellLayout).filter(CellLayout.processor_key == processor_key).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"No layout for '{processor_key}'")
    db.delete(obj)
    db.commit()


# ── Defaults endpoint ─────────────────────────────────────────────

@router.get("/defaults/{processor_key}")
def get_defaults(processor_key: str):
    """Return the hardcoded defaults for a processor so the editor can show them."""
    cls = _REGISTRY.get(processor_key)
    if cls is None:
        raise HTTPException(status_code=404, detail=f"Processor '{processor_key}' not registered")

    # Instantiate with dummy dirs to read class attributes
    proc = cls.__new__(cls)

    # Compute default text Y positions from the render_cell methods
    # These are the hardcoded mm offsets used in the original processors
    defaults = _extract_processor_defaults(processor_key, proc)
    return defaults


def _extract_processor_defaults(key: str, proc) -> dict:
    """Extract default layout values from processor class attributes."""
    cell_w = getattr(proc, 'cell_width_mm', 140)
    cell_h = getattr(proc, 'cell_height_mm', 90)

    # Default text positions (mm from cell top) — from the hardcoded values
    # These vary per processor family. We provide sensible defaults.
    is_large = 'large_stakes' in key
    is_small = 'small' in key and 'metal' not in key
    is_heart = 'heart' in key
    is_metal = 'metal' in key
    is_photo = 'photo' in key

    if is_large:
        l1y, l2y, l3y = 28.0, 50.0, 68.0
    elif is_small or is_heart:
        l1y = cell_h / 2 - 15
        l2y = cell_h / 2
        l3y = cell_h / 2 + (15 if is_heart else 10)
    elif is_metal:
        l1y = cell_h / 2 - 12
        l2y = cell_h / 2
        l3y = cell_h / 2 + 10
    else:
        l1y, l2y, l3y = 28.0, 45.0, 57.0

    return {
        "processor_key": key,
        "cell_width_mm": cell_w,
        "cell_height_mm": cell_h,
        "page_width_mm": getattr(proc, 'page_width_mm', 439.8),
        "page_height_mm": getattr(proc, 'page_height_mm', 289.9),
        "grid_cols": getattr(proc, 'grid_cols', 3),
        "grid_rows": getattr(proc, 'grid_rows', 3),
        "line1_y_mm": l1y,
        "line2_y_mm": l2y,
        "line3_y_mm": l3y,
        "line1_size_pt": getattr(proc, 'line1_size_pt', 20.4),
        "line2_size_pt": getattr(proc, 'line2_size_pt', 30.0),
        "line3_size_pt": getattr(proc, 'line3_size_pt', 13.2),
        "text_x_frac": 0.65 if is_photo else 0.5,
        "graphic_x_frac": 0.0,
        "graphic_y_frac": 0.0,
        "graphic_w_frac": 1.0,
        "graphic_h_frac": 1.0,
        "photo_x_frac": 0.05 if is_photo else None,
        "photo_y_frac": None,  # vertically centred dynamically
        "photo_w_frac": 0.35 if is_photo else None,
        "photo_h_frac": 0.6 if is_photo else None,
        "max_chars_line1": 30 if (is_small or is_heart or is_metal) else 40,
        "max_chars_line2": 30 if (is_small or is_heart or is_metal) else 40,
        "max_chars_line3": 30 if (is_small or is_heart or is_metal) else 40,
        "line3_max_rows": 5,
        "font_family": "Georgia",
        "text_fill": "black",
    }


# ── Live Preview ──────────────────────────────────────────────────

@router.get("/preview/{processor_key}")
def preview_layout(
    processor_key: str,
    # Layout override params (query string) — if not provided, use DB or defaults
    line1_y_mm: Optional[float] = None,
    line2_y_mm: Optional[float] = None,
    line3_y_mm: Optional[float] = None,
    line1_size_pt: Optional[float] = None,
    line2_size_pt: Optional[float] = None,
    line3_size_pt: Optional[float] = None,
    text_x_frac: Optional[float] = None,
    font_family: Optional[str] = None,
    text_fill: Optional[str] = None,
    photo_x_frac: Optional[float] = None,
    photo_y_frac: Optional[float] = None,
    photo_w_frac: Optional[float] = None,
    photo_h_frac: Optional[float] = None,
    # Sample data
    sample_line1: str = Query("In Loving Memory Of", alias="line1"),
    sample_line2: str = Query("John Smith", alias="line2"),
    sample_line3: str = Query("1950 - 2024\nForever in our hearts", alias="line3"),
    db: Session = Depends(get_db),
):
    """Generate a single-cell SVG preview with the given layout parameters."""
    cls = _REGISTRY.get(processor_key)
    if cls is None:
        raise HTTPException(status_code=404, detail=f"Processor '{processor_key}' not registered")

    proc = cls.__new__(cls)
    defaults = _extract_processor_defaults(processor_key, proc)

    # Merge: query params > DB layout > processor defaults
    db_layout = db.query(CellLayout).filter(CellLayout.processor_key == processor_key).first()

    def val(param_val, field_name):
        if param_val is not None:
            return param_val
        if db_layout and getattr(db_layout, field_name, None) is not None:
            return getattr(db_layout, field_name)
        return defaults.get(field_name)

    l1y = val(line1_y_mm, "line1_y_mm")
    l2y = val(line2_y_mm, "line2_y_mm")
    l3y = val(line3_y_mm, "line3_y_mm")
    l1pt = val(line1_size_pt, "line1_size_pt")
    l2pt = val(line2_size_pt, "line2_size_pt")
    l3pt = val(line3_size_pt, "line3_size_pt")
    tx = val(text_x_frac, "text_x_frac")
    ff = val(font_family, "font_family")
    tf = val(text_fill, "text_fill")

    cell_w = defaults["cell_width_mm"]
    cell_h = defaults["cell_height_mm"]
    cell_w_px = cell_w * PX_PER_MM
    cell_h_px = cell_h * PX_PER_MM
    margin = 2  # mm
    svg_w = cell_w + margin * 2
    svg_h = cell_h + margin * 2

    dwg = svgwrite.Drawing(
        size=(f"{svg_w}mm", f"{svg_h}mm"),
        viewBox=f"0 0 {svg_w * PX_PER_MM} {svg_h * PX_PER_MM}",
    )

    ox = margin * PX_PER_MM
    oy = margin * PX_PER_MM

    # Cell border
    dwg.add(dwg.rect(
        insert=(ox, oy), size=(cell_w_px, cell_h_px),
        rx=6 * PX_PER_MM, ry=6 * PX_PER_MM,
        fill="#f8f8f8", stroke="red", stroke_width=0.3 * PX_PER_MM,
    ))

    # Guide lines for text positions (dashed)
    for y_mm, color, label in [
        (l1y, "#3b82f6", "L1"),
        (l2y, "#10b981", "L2"),
        (l3y, "#f59e0b", "L3"),
    ]:
        y_px = oy + y_mm * PX_PER_MM
        dwg.add(dwg.line(
            start=(ox, y_px), end=(ox + cell_w_px, y_px),
            stroke=color, stroke_width=0.15 * PX_PER_MM,
            stroke_dasharray="2,2",
        ))
        dwg.add(dwg.text(
            label, insert=(ox + 1 * PX_PER_MM, y_px - 1 * PX_PER_MM),
            font_size="2mm", fill=color, font_family="sans-serif",
        ))

    center_x = ox + cell_w_px * tx

    # Line 1
    if sample_line1:
        dwg.add(dwg.text(
            sample_line1,
            insert=(center_x, oy + l1y * PX_PER_MM),
            font_size=f"{l1pt * PT_TO_MM}mm",
            font_family=ff, text_anchor="middle", fill=tf,
        ))

    # Line 2
    if sample_line2:
        dwg.add(dwg.text(
            sample_line2,
            insert=(center_x, oy + l2y * PX_PER_MM),
            font_size=f"{l2pt * PT_TO_MM}mm",
            font_family=ff, text_anchor="middle", fill=tf,
        ))

    # Line 3
    if sample_line3:
        lines = []
        for raw in sample_line3.split("\n"):
            if raw.strip():
                lines.extend(split_line_to_fit(raw, defaults.get("max_chars_line3", 40)))
        lines = lines[:defaults.get("line3_max_rows", 5)]
        if lines:
            el = dwg.text(
                "", insert=(center_x, oy + l3y * PX_PER_MM),
                font_size=f"{l3pt * PT_TO_MM}mm",
                font_family=ff, text_anchor="middle", fill=tf,
            )
            for i, ln in enumerate(lines):
                el.add(dwg.tspan(ln.strip(), x=[center_x],
                                 dy=["0" if i == 0 else "1.2em"]))
            dwg.add(el)

    svg_bytes = dwg.tostring().encode("utf-8")
    return Response(content=svg_bytes, media_type="image/svg+xml")
