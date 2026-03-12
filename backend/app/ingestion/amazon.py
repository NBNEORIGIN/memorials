"""Amazon order ingestion pipeline.

Ported from AmazonPhotoProcessor 2 / order_pipeline.py.
Handles: parsing tab-delimited reports, downloading customisation ZIPs,
extracting XML personalisation data and photos.
"""

import csv
import io
import os
import re
import shutil
import tempfile
import zipfile
from typing import Optional

import requests

from app.ingestion.xml_parser import parse_xml_for_fields


def extract_orders_from_report(report_path: str) -> list[dict]:
    """Parse a tab-delimited Amazon order report, extracting rows with customised-url."""
    orders = []
    with open(report_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            zip_url = row.get("customized-url", "").strip()
            orders.append({
                "order-id": row.get("order-id", "").strip(),
                "order-item-id": row.get("order-item-id", "").strip(),
                "sku": row.get("sku", "").strip(),
                "number-of-items": row.get("number-of-items", "1").strip(),
                "zip_url": zip_url if zip_url.startswith("http") else "",
            })
    return orders


def download_and_extract_zip(url: str, dest_folder: str) -> bool:
    """Download a ZIP from URL and extract to dest_folder."""
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(dest_folder)
        return True
    except Exception as e:
        print(f"ZIP download failed: {url} -> {e}")
        return False


def process_order_personalisation(
    order: dict,
    downloads_dir: str,
    images_dir: str,
) -> dict:
    """Download the customisation ZIP for a single order, extract XML/image data.

    Returns dict with keys: graphic, line_1, line_2, line_3, image_path
    """
    result = {"graphic": "", "line_1": "", "line_2": "", "line_3": "", "image_path": ""}

    zip_url = order.get("zip_url", "")
    if not zip_url:
        return result

    order_folder = os.path.join(
        downloads_dir,
        f"{order['order-id']}_{order['order-item-id']}",
    )
    os.makedirs(order_folder, exist_ok=True)

    if not download_and_extract_zip(zip_url, order_folder):
        return result

    # Parse XML for personalisation fields
    xml_files = [f for f in os.listdir(order_folder) if f.endswith(".xml")]
    if xml_files:
        xml_path = os.path.join(order_folder, xml_files[0])
        graphic, line_1, line_2, line_3 = parse_xml_for_fields(xml_path)
        # Append .png to graphic name if present
        result["graphic"] = (graphic + ".png") if graphic else ""
        result["line_1"] = line_1
        result["line_2"] = line_2
        result["line_3"] = line_3

    # Extract largest JPG as the photo
    jpg_files = [f for f in os.listdir(order_folder) if f.lower().endswith(".jpg")]
    if jpg_files:
        jpg_paths = [os.path.join(order_folder, f) for f in jpg_files]
        largest = max(jpg_paths, key=os.path.getsize)
        new_name = f"{order['order-item-id']}.jpg"
        dest_path = os.path.join(images_dir, new_name)
        try:
            shutil.copy2(largest, dest_path)
            result["image_path"] = dest_path
        except Exception as e:
            print(f"Image copy failed: {e}")

    return result


def process_report_file(
    report_path: str,
    images_dir: str,
) -> list[dict]:
    """Full pipeline: parse report → download ZIPs → extract personalisation data.

    Returns list of enriched order item dicts ready for DB insertion.
    """
    orders = extract_orders_from_report(report_path)
    temp_dir = tempfile.mkdtemp()
    downloads_dir = os.path.join(temp_dir, "downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    enriched = []
    for i, order in enumerate(orders):
        # Expand by quantity
        try:
            qty = max(int(order.get("number-of-items", "1")), 1)
        except (ValueError, TypeError):
            qty = 1

        # Download personalisation data (once per order-item)
        personalisation = process_order_personalisation(order, downloads_dir, images_dir)

        for _ in range(qty):
            item = {
                "order-id": order["order-id"],
                "order-item-id": order["order-item-id"],
                "sku": order["sku"],
                "quantity": 1,
                "graphic": personalisation["graphic"],
                "line_1": personalisation["line_1"],
                "line_2": personalisation["line_2"],
                "line_3": personalisation["line_3"],
                "image_path": personalisation["image_path"],
            }
            enriched.append(item)

    # Clean up temp dir
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    return enriched


def generate_warnings(item: dict) -> str:
    """Generate quality warnings for text lines (spacing, case, dates)."""
    warnings = []
    for key in ("line_1", "line_2", "line_3"):
        value = item.get(key, "")
        if not value:
            continue
        if re.search(r"\s+[,.]", value):
            warnings.append(f"Extra space before punctuation in {key}")
        if re.search(r"[a-zA-Z],[a-zA-Z]", value):
            warnings.append(f"Missing space after comma in {key}")
        if "  " in value:
            warnings.append(f"Double space in {key}")
        if re.search(r"\b(\w+) \1\b", value, re.IGNORECASE):
            warnings.append(f"Repeated word in {key}")
    return "; ".join(warnings)
