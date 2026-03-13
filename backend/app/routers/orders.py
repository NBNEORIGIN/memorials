"""Order ingestion — upload Amazon .txt files, parse, resolve SKUs, create job items."""

import os
import shutil
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.models import Job, JobItem, SkuMapping
from app.schemas import JobOut, JobSummaryOut, JobItemOut, JobItemUpdate
from app.ingestion.amazon import process_report_file

router = APIRouter(prefix="/api/jobs", tags=["Order Processing"])


@router.get("/", response_model=list[JobSummaryOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).order_by(Job.created_at.desc()).limit(50).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).options(joinedload(Job.items)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/upload", response_model=JobOut)
async def upload_order_file(
    file: UploadFile = File(...),
    enrich: bool = Query(True, description="Download ZIPs and extract XML personalisation data"),
    db: Session = Depends(get_db),
):
    """Upload an Amazon order .txt file. Parses orders, resolves SKUs, creates job items.

    When enrich=True (default), downloads customisation ZIPs from Amazon,
    extracts XML personalisation data (graphic, lines, photos).
    Set enrich=False for quick parsing without downloads.
    """
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files accepted")

    # Save uploaded file
    upload_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Parse the tab-delimited Amazon order file
    try:
        if enrich:
            images_dir = os.path.join(settings.UPLOAD_DIR, "images")
            items_data = process_report_file(upload_path, images_dir)
        else:
            items_data = parse_amazon_txt(upload_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {e}")

    # Create job
    job = Job(source="amazon", filename=file.filename, item_count=len(items_data))
    db.add(job)
    db.flush()

    # Resolve each item against SKU mappings
    for item_data in items_data:
        sku = item_data.get("sku", "").strip()
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

        job_item = JobItem(
            job_id=job.id,
            order_id=item_data.get("order-id"),
            order_item_id=item_data.get("order-item-id"),
            sku=sku,
            quantity=int(item_data.get("quantity", 1)),
            graphic=item_data.get("graphic"),
            line_1=item_data.get("line_1"),
            line_2=item_data.get("line_2"),
            line_3=item_data.get("line_3"),
            image_path=item_data.get("image_path"),
        )

        if mapping:
            job_item.colour = mapping.colour.name
            job_item.memorial_type = mapping.memorial_type.name
            job_item.decoration_type = mapping.decoration_type.name if mapping.decoration_type else None
            job_item.theme = mapping.theme.name if mapping.theme else None
            job_item.processor_key = mapping.processor.key
            job_item.status = "ready"
        else:
            job_item.status = "unmatched"
            job_item.error = f"SKU '{sku}' not found in database"

        db.add(job_item)

    job.status = "parsed"
    db.commit()
    db.refresh(job)

    # Re-query with items loaded
    return get_job(job.id, db)


def _resolve_and_add_items(db: Session, job: Job, items_data: list[dict]):
    """Resolve SKU mappings and add JobItem rows to a job."""
    for item_data in items_data:
        sku = item_data.get("sku", "").strip()
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

        job_item = JobItem(
            job_id=job.id,
            order_id=item_data.get("order-id"),
            order_item_id=item_data.get("order-item-id"),
            sku=sku,
            quantity=int(item_data.get("quantity", 1)),
            graphic=item_data.get("graphic"),
            line_1=item_data.get("line_1"),
            line_2=item_data.get("line_2"),
            line_3=item_data.get("line_3"),
            image_path=item_data.get("image_path"),
        )

        if mapping:
            job_item.colour = mapping.colour.name
            job_item.memorial_type = mapping.memorial_type.name
            job_item.decoration_type = mapping.decoration_type.name if mapping.decoration_type else None
            job_item.theme = mapping.theme.name if mapping.theme else None
            job_item.processor_key = mapping.processor.key
            job_item.status = "ready"
        else:
            job_item.status = "unmatched"
            job_item.error = f"SKU '{sku}' not found in database"

        db.add(job_item)


@router.post("/upload-multi", response_model=JobOut)
async def upload_multi_order_files(
    files: List[UploadFile] = File(...),
    enrich: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Upload multiple Amazon order .txt files and merge into a single job.

    Use when orders come from different Amazon accounts/regions.
    All items from all files are combined into one job.
    """
    txt_files = [f for f in files if f.filename and f.filename.lower().endswith(".txt")]
    if not txt_files:
        raise HTTPException(status_code=400, detail="No .txt files provided")

    all_items: list[dict] = []
    filenames: list[str] = []

    for uploaded in txt_files:
        upload_path = os.path.join(settings.UPLOAD_DIR, uploaded.filename)
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(uploaded.file, f)
        filenames.append(uploaded.filename)

        try:
            if enrich:
                images_dir = os.path.join(settings.UPLOAD_DIR, "images")
                items_data = process_report_file(upload_path, images_dir)
            else:
                items_data = parse_amazon_txt(upload_path)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to parse {uploaded.filename}: {e}")

        all_items.extend(items_data)

    # Create single merged job
    combined_name = " + ".join(filenames)
    job = Job(source="amazon", filename=combined_name, item_count=len(all_items))
    db.add(job)
    db.flush()

    _resolve_and_add_items(db, job, all_items)
    job.item_count = len(all_items)
    job.status = "parsed"
    db.commit()
    db.refresh(job)

    return get_job(job.id, db)


@router.patch("/items/{item_id}", response_model=JobItemOut)
def update_job_item(item_id: int, body: JobItemUpdate, db: Session = Depends(get_db)):
    """Update personalisation fields on a job item (inline editing)."""
    item = db.query(JobItem).filter(JobItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()


def parse_amazon_txt(filepath: str) -> list[dict]:
    """Parse a tab-delimited Amazon order .txt file into a list of item dicts.

    Expected columns: order-id, order-item-id, sku, quantity,
    plus customisation fields extracted from XML if present.
    """
    import pandas as pd

    df = pd.read_csv(filepath, sep="\t", dtype=str, encoding="utf-8")
    df = df.fillna("")

    items = []
    for _, row in df.iterrows():
        # Expand by quantity (number-of-items)
        try:
            qty = max(int(row.get("number-of-items", 1)), 1)
        except (ValueError, TypeError):
            qty = 1

        for _ in range(qty):
            item = {
                "order-id": row.get("order-id", ""),
                "order-item-id": row.get("order-item-id", ""),
                "sku": row.get("sku", ""),
                "quantity": 1,
            }

            # Customisation fields may be in various columns
            # These will be populated by the XML parser in a later step
            for field in ["graphic", "line_1", "line_2", "line_3", "image_path"]:
                item[field] = row.get(field, "")

            items.append(item)

    return items
