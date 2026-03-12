"""Base processor class. All SVG processors inherit from this.

Each processor receives ONLY its own items (pre-filtered by the dispatcher).
Processors are stateless — no shared mutable state between processors.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderItem:
    """Standardised order item passed to every processor."""
    order_id: str
    order_item_id: str
    sku: str
    colour: str
    memorial_type: str
    decoration_type: Optional[str]
    theme: Optional[str]
    graphic: Optional[str]
    line_1: Optional[str]
    line_2: Optional[str]
    line_3: Optional[str]
    image_path: Optional[str]


@dataclass
class ProcessorResult:
    """Result from processing a single item."""
    success: bool
    svg_path: Optional[str] = None
    error: Optional[str] = None


class BaseProcessor(ABC):
    """Abstract base for all SVG processors.

    Subclasses must implement:
        - generate_svg(item, output_dir) -> ProcessorResult
    """

    # Subclasses set these
    processor_key: str = ""
    display_name: str = ""

    def __init__(self, graphics_dir: str, output_dir: str):
        self.graphics_dir = graphics_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    @abstractmethod
    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        """Generate an SVG file for a single order item.

        Args:
            item: Standardised order item with all personalisation data.
            output_dir: Directory to write the SVG file to.

        Returns:
            ProcessorResult with success status and output path.
        """
        ...

    def build_filename(self, item: OrderItem) -> str:
        """Build a descriptive SVG filename from order item data."""
        parts = [
            item.order_id or "NOID",
            item.sku or "NOSKU",
            item.memorial_type or "",
            item.colour or "",
        ]
        if item.graphic:
            g = item.graphic
            if g.lower().endswith(".png"):
                g = g[:-4]
            parts.append(g)
        name = " ".join(p for p in parts if p).strip()
        # Sanitise filename
        name = "".join(c if c.isalnum() or c in " -_" else "_" for c in name)
        return f"{name}.svg"
