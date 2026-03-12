"""SVG generation endpoint — dispatches job items to their assigned processors."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.models import Job, JobItem
from app.schemas import JobOut
from app.processors.base import OrderItem
from app.processors.registry import get_processor

router = APIRouter(prefix="/api/generate", tags=["SVG Generation"])


@router.post("/{job_id}", response_model=JobOut)
def generate_svgs(job_id: int, db: Session = Depends(get_db)):
    """Generate SVGs for all ready items in a job."""
    job = db.query(Job).options(joinedload(Job.items)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in ("parsed", "partial"):
        raise HTTPException(status_code=400, detail=f"Job status is '{job.status}', expected 'parsed'")

    job.status = "processing"
    db.flush()

    success_count = 0
    error_count = 0
    graphics_dir = settings.UPLOAD_DIR  # Graphics loaded from uploads or assets

    for item in job.items:
        if item.status != "ready":
            continue

        if not item.processor_key:
            item.status = "error"
            item.error = "No processor assigned"
            error_count += 1
            continue

        processor = get_processor(item.processor_key, graphics_dir, settings.OUTPUT_DIR)
        if processor is None:
            item.status = "error"
            item.error = f"Processor '{item.processor_key}' not registered"
            error_count += 1
            continue

        order_item = OrderItem(
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

        try:
            result = processor.generate_svg(order_item, settings.OUTPUT_DIR)
            if result.success:
                item.status = "complete"
                item.svg_path = result.svg_path
                success_count += 1
            else:
                item.status = "error"
                item.error = result.error or "Unknown processor error"
                error_count += 1
        except Exception as e:
            item.status = "error"
            item.error = str(e)
            error_count += 1

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
