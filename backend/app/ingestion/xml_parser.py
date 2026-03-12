"""XML parser for Amazon personalisation data.

Ported from AmazonPhotoProcessor 2 / order_pipeline.py — parse_xml_for_fields().
Extracts graphic name and text lines (Line 1, Line 2, Line 3) from Amazon
customisation XML files.
"""

import xml.etree.ElementTree as ET


def parse_xml_for_fields(xml_path: str) -> tuple[str, str, str, str]:
    """Parse an Amazon personalisation XML file.

    Returns:
        (graphic, line_1, line_2, line_3) — all strings, empty if not found.
    """
    with open(xml_path, "rb") as f:
        xml_text = f.read().decode("utf-8")
    root = ET.fromstring(xml_text)

    graphic = _extract_graphic(root)
    line_1 = _extract_line(root, "Line 1")
    line_2 = _extract_line(root, "Line 2")
    line_3 = _extract_line(root, "Line 3")

    return graphic, line_1, line_2, line_3


def _extract_graphic(root: ET.Element) -> str:
    """Extract the Graphic field from areas elements."""
    # First pass: look in areas/label == "Graphic"
    for area in root.findall(".//areas"):
        label = area.find("label")
        if label is not None and label.text == "Graphic":
            for tag in ("optionValue", "displayValue"):
                elem = area.find(tag)
                if elem is not None and elem.text:
                    return elem.text.strip()

    # Fallback: iterate all elements looking for label "Graphic"
    for elem in root.iter():
        if elem.tag == "label" and elem.text == "Graphic":
            parent = _get_parent(root, elem)
            if parent is not None:
                for sibling in parent:
                    if sibling.tag in ("displayValue", "optionValue") and sibling.text:
                        return sibling.text.strip()

    return ""


def _extract_line(root: ET.Element, line_label: str) -> str:
    """Extract a text line (Line 1/2/3) from areas elements."""
    # First pass: areas/label match
    for area in root.findall(".//areas"):
        label = area.find("label")
        if label is not None and label.text == line_label:
            text_elem = area.find("text")
            if text_elem is not None and text_elem.text:
                return text_elem.text.strip()

    # Fallback: iterate all elements
    for elem in root.iter():
        if elem.tag == "label" and elem.text == line_label:
            parent = _get_parent(root, elem)
            if parent is not None:
                for sibling in parent:
                    if sibling.tag in ("inputValue", "text") and sibling.text:
                        return sibling.text.strip()

    return ""


def _get_parent(root: ET.Element, child: ET.Element) -> ET.Element | None:
    """Find parent of a child element (ET doesn't have getparent())."""
    parent_map = {c: p for p in root.iter() for c in p}
    return parent_map.get(child)
