"""Base processor class. All SVG processors inherit from this.

Each processor receives ONLY its own items (pre-filtered by the dispatcher).
Processors are stateless — no shared mutable state between processors.

Print sheets: Items are batched into grid layouts on a full print page.
Regular stakes = 3×3 (9 per page), large stakes = 2×2 (4 per page), etc.
"""

import os
import base64
import mimetypes
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import svgwrite


PX_PER_MM = 1 / 0.26458333333   # ≈ 3.7795
PT_TO_MM = 0.2645833333


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
    layout_overrides: Optional[dict] = None


@dataclass
class ProcessorResult:
    """Result from processing a single item."""
    success: bool
    svg_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class BatchResult:
    """Result from generating a batch print sheet."""
    success: bool
    svg_path: Optional[str] = None
    item_ids: List[int] = field(default_factory=list)
    error: Optional[str] = None


def embed_image(image_path: str) -> Optional[str]:
    """Read an image file and return a base64 data URI for SVG embedding."""
    norm = os.path.normpath(image_path)
    if not os.path.exists(norm):
        return None
    try:
        mime = mimetypes.guess_type(norm)[0] or "image/png"
        with open(norm, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f"data:{mime};base64,{data}"
    except Exception:
        return None


def split_line_to_fit(text: str, max_chars: int = 40) -> List[str]:
    """Word-wrap a single line of text to fit within max_chars."""
    if not text or not text.strip():
        return []
    result = []
    for line in str(text).split("\n"):
        if not line.strip():
            result.append("")
            continue
        if len(line) <= max_chars:
            result.append(line)
        else:
            current: List[str] = []
            for word in line.split():
                if current and len(" ".join(current + [word])) > max_chars:
                    result.append(" ".join(current))
                    current = [word]
                else:
                    current.append(word)
            if current:
                result.append(" ".join(current))
    return result


def estimate_text_width_mm(text: str, font_size_pt: float) -> float:
    """Rough estimate of text width in mm for a given font size.

    Uses average character width ≈ 0.52 × font size in mm for Georgia.
    This is an approximation — real width varies per character.
    """
    char_width_mm = font_size_pt * PT_TO_MM * 0.52
    return len(text) * char_width_mm


def estimate_max_chars(available_width_mm: float, font_size_pt: float) -> int:
    """Estimate how many chars fit in a given width at a given font size."""
    char_width_mm = font_size_pt * PT_TO_MM * 0.52
    if char_width_mm <= 0:
        return 40
    return max(8, int(available_width_mm / char_width_mm))


def smart_wrap_text(
    text: str,
    available_width_mm: float,
    font_size_pt: float,
    max_rows: int = 6,
    min_font_pt: float = 8.0,
    shrink_step_pt: float = 1.0,
) -> tuple:
    """Smart text wrapping that respects intentional line breaks and adapts font size.

    Returns (lines: list[str], final_font_pt: float).

    Strategy:
    1. Respect customer newlines (poems, dates on separate lines).
    2. Word-wrap each line to fit available width.
    3. If too many lines, shrink font and retry.
    4. Never go below min_font_pt.
    """
    if not text or not text.strip():
        return [], font_size_pt

    current_pt = font_size_pt

    while current_pt >= min_font_pt:
        max_chars = estimate_max_chars(available_width_mm, current_pt)
        lines = []
        for raw_line in str(text).split("\n"):
            stripped = raw_line.strip()
            if not stripped:
                continue
            if len(stripped) <= max_chars:
                lines.append(stripped)
            else:
                # Word-wrap this line
                current_words: List[str] = []
                for word in stripped.split():
                    if current_words and len(" ".join(current_words + [word])) > max_chars:
                        lines.append(" ".join(current_words))
                        current_words = [word]
                    else:
                        current_words.append(word)
                if current_words:
                    lines.append(" ".join(current_words))

        if len(lines) <= max_rows:
            return lines, current_pt

        # Too many lines — shrink font and retry
        current_pt -= shrink_step_pt

    # Hit min font — just truncate to max_rows at min size
    max_chars = estimate_max_chars(available_width_mm, min_font_pt)
    lines = []
    for raw_line in str(text).split("\n"):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if len(stripped) <= max_chars:
            lines.append(stripped)
        else:
            current_words: List[str] = []
            for word in stripped.split():
                if current_words and len(" ".join(current_words + [word])) > max_chars:
                    lines.append(" ".join(current_words))
                    current_words = [word]
                else:
                    current_words.append(word)
            if current_words:
                lines.append(" ".join(current_words))
    return lines[:max_rows], min_font_pt


class BaseProcessor(ABC):
    """Abstract base for all SVG processors.

    Subclasses define the page dimensions, cell dimensions, grid layout,
    and how each cell is rendered. The base class handles batching items
    into print sheets and creating the SVG page scaffold.
    """

    # Subclasses set these
    processor_key: str = ""
    display_name: str = ""

    # Page dimensions in mm (override per processor)
    page_width_mm: float = 439.8
    page_height_mm: float = 289.9

    # Memorial cell dimensions in mm (override per processor)
    cell_width_mm: float = 140
    cell_height_mm: float = 90

    # Grid layout (override per processor)
    grid_cols: int = 3
    grid_rows: int = 3

    # Corner radius for cell border in mm
    corner_radius_mm: float = 6

    # Text sizes in pt (override per processor)
    line1_size_pt: float = 17 * 1.2   # heading
    line2_size_pt: float = 25 * 1.2   # name (large)
    line3_size_pt: float = 12 * 1.1   # additional text

    # Stroke width in mm
    stroke_width_mm: float = 0.1

    def __init__(self, graphics_dir: str, output_dir: str, layout_overrides: Optional[dict] = None):
        self.graphics_dir = graphics_dir
        self.output_dir = output_dir
        self.layout_overrides = layout_overrides or {}
        os.makedirs(output_dir, exist_ok=True)

    def lv(self, field: str, default=None):
        """Resolve a layout value: DB override → class attribute → default."""
        v = self.layout_overrides.get(field)
        if v is not None:
            return v
        v = getattr(self, field, None)
        if v is not None:
            return v
        return default

    @property
    def batch_size(self) -> int:
        return self.grid_cols * self.grid_rows

    # ── Pixel conversions ──────────────────────────────────────────
    @property
    def page_width_px(self) -> float:
        return self.page_width_mm * PX_PER_MM

    @property
    def page_height_px(self) -> float:
        return self.page_height_mm * PX_PER_MM

    @property
    def cell_width_px(self) -> float:
        return self.cell_width_mm * PX_PER_MM

    @property
    def cell_height_px(self) -> float:
        return self.cell_height_mm * PX_PER_MM

    @property
    def x_offset_px(self) -> float:
        """Horizontal offset to centre the grid on the page."""
        grid_w = self.cell_width_mm * self.grid_cols
        return ((self.page_width_mm - grid_w) / 2) * PX_PER_MM

    @property
    def y_offset_px(self) -> float:
        """Vertical offset to centre the grid on the page."""
        grid_h = self.cell_height_mm * self.grid_rows
        return ((self.page_height_mm - grid_h) / 2) * PX_PER_MM

    # ── Batch SVG generation ──────────────────────────────────────
    def generate_batch_svg(self, items: List[OrderItem],
                           batch_num: int, output_dir: str) -> BatchResult:
        """Generate a single print-sheet SVG containing up to batch_size items."""
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.processor_key}_{ts}_{batch_num:03d}.svg"
            filepath = os.path.join(output_dir, filename)

            dwg = svgwrite.Drawing(
                filename=filepath,
                size=(f"{self.page_width_mm}mm", f"{self.page_height_mm}mm"),
                viewBox=f"0 0 {self.page_width_px} {self.page_height_px}",
            )

            for idx in range(self.batch_size):
                row = idx // self.grid_cols
                col = idx % self.grid_cols

                x = self.x_offset_px + col * self.cell_width_px
                y = self.y_offset_px + row * self.cell_height_px

                # Determine border colour
                stroke_colour = "red"
                if idx < len(items):
                    item = items[idx]
                    c = (item.colour or "").lower()
                    t = (item.memorial_type or "").lower()
                    if c in ("marble", "stone") or t == "regular plaque":
                        stroke_colour = "yellow"

                # Cell border (rounded rect)
                dwg.add(dwg.rect(
                    insert=(x, y),
                    size=(self.cell_width_px, self.cell_height_px),
                    rx=self.corner_radius_mm * PX_PER_MM,
                    ry=self.corner_radius_mm * PX_PER_MM,
                    fill="none",
                    stroke=stroke_colour,
                    stroke_width=self.stroke_width_mm * PX_PER_MM,
                ))

                # Render the item content into this cell
                if idx < len(items):
                    self.render_cell(dwg, items[idx], x, y)

            # Reference point (0.1mm blue square, bottom-right corner)
            ref = 0.1 * PX_PER_MM
            dwg.add(dwg.rect(
                insert=(self.page_width_px - ref, self.page_height_px - ref),
                size=(ref, ref), fill="blue",
            ))

            dwg.save()
            return BatchResult(success=True, svg_path=filepath)

        except Exception as e:
            return BatchResult(success=False, error=str(e))

    @abstractmethod
    def render_cell(self, dwg: svgwrite.Drawing, item: OrderItem,
                    x: float, y: float) -> None:
        """Render a single memorial item into a cell at position (x, y) in pixels.

        Subclasses implement the actual graphic embedding, text layout, etc.
        """
        ...

    # ── Legacy single-item interface (calls batch with 1 item) ────
    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        """Generate SVG for a single item (wraps batch generation)."""
        result = self.generate_batch_svg([item], 1, output_dir)
        return ProcessorResult(
            success=result.success,
            svg_path=result.svg_path,
            error=result.error,
        )
