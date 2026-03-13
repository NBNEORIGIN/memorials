"""SVG generation endpoint — batches job items by processor type into print sheets."""

import io
import os
import zipfile
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.models import Job, JobItem, CellLayout
from app.schemas import JobOut
from app.processors.base import OrderItem
from app.processors.registry import get_processor


def _load_layout_overrides(db: Session, processor_key: str) -> dict:
    """Load CellLayout from DB and return as dict of non-None overrides."""
    layout = db.query(CellLayout).filter(CellLayout.processor_key == processor_key).first()
    if not layout:
        return {}
    overrides = {}
    for field in (
        "line1_y_mm", "line2_y_mm", "line3_y_mm",
        "line1_size_pt", "line2_size_pt", "line3_size_pt",
        "text_x_frac",
        "graphic_x_frac", "graphic_y_frac", "graphic_w_frac", "graphic_h_frac",
        "photo_x_frac", "photo_y_frac", "photo_w_frac", "photo_h_frac",
        "max_chars_line1", "max_chars_line2", "max_chars_line3",
        "line3_max_rows", "font_family", "text_fill",
    ):
        v = getattr(layout, field, None)
        if v is not None:
            overrides[field] = v
    return overrides

router = APIRouter(prefix="/api/generate", tags=["SVG Generation"])


def _build_order_item(item: JobItem) -> OrderItem:
    return OrderItem(
        order_id=item.order_id or "",
        order_item_id=item.order_item_id or "",
        sku=item.sku,
        colour=item.colour or "",
        memorial_type=item.memorial_type or "",
        decoration_type=item.decoration_type,
        theme=item.theme,
        graphic=item.graphic,
        line_1=item.line_1,
        line_2=item.line_2,
        line_3=item.line_3,
        image_path=item.image_path,
    )


@router.post("/{job_id}", response_model=JobOut)
def generate_svgs(job_id: int, db: Session = Depends(get_db)):
    """Generate batch print-sheet SVGs for all ready items in a job.

    Items are grouped by processor_key, then batched into print sheets
    (e.g. 9 regular stakes per page, 4 large stakes per page, etc.).
    All items in a batch share the same SVG file path.
    """
    job = db.query(Job).options(joinedload(Job.items)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in ("parsed", "partial", "complete", "failed"):
        raise HTTPException(status_code=400, detail=f"Job status is '{job.status}', cannot generate")

    job.status = "processing"
    db.flush()

    success_count = 0
    error_count = 0
    graphics_dir = settings.GRAPHICS_DIR

    # ── Group ready items by processor_key ────────────────────────
    groups: Dict[str, List[JobItem]] = defaultdict(list)
    for item in job.items:
        if item.status != "ready":
            continue
        if not item.processor_key:
            item.status = "error"
            item.error = "No processor assigned"
            error_count += 1
            continue
        groups[item.processor_key].append(item)

    # ── Generate batch print sheets per processor type ────────────
    for proc_key, db_items in groups.items():
        overrides = _load_layout_overrides(db, proc_key)
        processor = get_processor(proc_key, graphics_dir, settings.OUTPUT_DIR,
                                  layout_overrides=overrides)
        if processor is None:
            for it in db_items:
                it.status = "error"
                it.error = f"Processor '{proc_key}' not registered"
                error_count += 1
            continue

        # Sort by colour priority (copper→gold→silver→stone→marble)
        colour_order = {"copper": 0, "gold": 1, "silver": 2, "stone": 3, "marble": 4}
        db_items.sort(key=lambda it: colour_order.get((it.colour or "").lower(), 99))

        # Build OrderItem objects, keeping parallel index with db_items
        order_items = [_build_order_item(it) for it in db_items]

        batch_size = processor.batch_size
        batch_num = 1

        for start in range(0, len(order_items), batch_size):
            batch_order_items = order_items[start:start + batch_size]
            batch_db_items = db_items[start:start + batch_size]

            try:
                result = processor.generate_batch_svg(
                    batch_order_items, batch_num, settings.OUTPUT_DIR,
                )
                if result.success:
                    for it in batch_db_items:
                        it.status = "complete"
                        it.svg_path = result.svg_path
                    success_count += len(batch_db_items)
                else:
                    for it in batch_db_items:
                        it.status = "error"
                        it.error = result.error or "Unknown batch error"
                    error_count += len(batch_db_items)
            except Exception as e:
                for it in batch_db_items:
                    it.status = "error"
                    it.error = str(e)
                error_count += len(batch_db_items)

            batch_num += 1

    # ── Update job status ─────────────────────────────────────────
    if error_count == 0:
        job.status = "complete"
    elif success_count > 0:
        job.status = "partial"
    else:
        job.status = "failed"

    job.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    return db.query(Job).options(joinedload(Job.items)).filter(Job.id == job_id).first()


@router.post("/reset/{job_id}", response_model=JobOut)
def reset_job(job_id: int, db: Session = Depends(get_db)):
    """Reset all items in a job back to 'ready' so they can be re-generated."""
    job = db.query(Job).options(joinedload(Job.items)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    for item in job.items:
        if item.status in ("complete", "error"):
            item.status = "ready"
            item.svg_path = None
            item.error = None

    job.status = "parsed"
    job.completed_at = None
    db.commit()
    db.refresh(job)
    return db.query(Job).options(joinedload(Job.items)).filter(Job.id == job_id).first()


@router.get("/svg/{item_id}")
def get_svg_file(item_id: int, db: Session = Depends(get_db)):
    """Serve a generated SVG file for preview or download."""
    item = db.query(JobItem).filter(JobItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item.svg_path or not os.path.exists(item.svg_path):
        raise HTTPException(status_code=404, detail="SVG file not found")
    return FileResponse(item.svg_path, media_type="image/svg+xml",
                        filename=os.path.basename(item.svg_path))


@router.get("/download/{job_id}")
def download_all_svgs(job_id: int, db: Session = Depends(get_db)):
    """Download all generated SVGs for a job as a ZIP file."""
    job = db.query(Job).options(joinedload(Job.items)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    completed = [i for i in job.items if i.status == "complete" and i.svg_path and os.path.exists(i.svg_path)]
    if not completed:
        raise HTTPException(status_code=404, detail="No completed SVG files to download")

    # Deduplicate — batch sheets are shared by multiple items
    seen_paths: set[str] = set()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in completed:
            if item.svg_path not in seen_paths:
                seen_paths.add(item.svg_path)
                zf.write(item.svg_path, os.path.basename(item.svg_path))
    buf.seek(0)

    filename = f"{job.filename or f'job_{job.id}'}_svgs.zip"
    return StreamingResponse(
        buf, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
