"""Brass Plaque / Laser Engrave processors.

These produce text-only SVGs for laser engraving on brass plaques.
No graphic backgrounds — just centred text with a plaque outline.
Uses single-row layout (like metal stakes) with configurable part sizes.
"""

import os
import svgwrite

from app.processors.base import (
    BaseProcessor, OrderItem, PX_PER_MM, PT_TO_MM,
    embed_image, split_line_to_fit,
)
from app.processors.registry import register


def _render_brass_cell(
    dwg, item, x, y, graphics_dir, cell_w_px, cell_h_px,
    text_fill="black", layout=None,
):
    """Render a brass plaque cell — outline border + centred text only.

    For laser engraving: no graphic background, clean text layout.
    """
    lo = layout or {}
    cell_w_mm = cell_w_px / PX_PER_MM
    cell_h_mm = cell_h_px / PX_PER_MM
    l1y = lo.get("line1_y_mm", cell_h_mm * 0.25)
    l2y = lo.get("line2_y_mm", cell_h_mm * 0.50)
    l3y = lo.get("line3_y_mm", cell_h_mm * 0.72)
    l1pt = lo.get("line1_size_pt", 14.0)
    l2pt = lo.get("line2_size_pt", 20.0)
    l3pt = lo.get("line3_size_pt", 10.0)
    tx = lo.get("text_x_frac", 0.5)
    ff = lo.get("font_family", "Georgia")
    tf = lo.get("text_fill", text_fill)
    max_chars = lo.get("max_chars_line3", 35)
    max_rows = lo.get("line3_max_rows", 4)
    border_mm = 2.0  # inset border

    # Plaque outline — double border for brass look
    bpx = border_mm * PX_PER_MM
    dwg.add(dwg.rect(
        insert=(x + bpx, y + bpx),
        size=(cell_w_px - 2 * bpx, cell_h_px - 2 * bpx),
        rx=1.5 * PX_PER_MM, ry=1.5 * PX_PER_MM,
        fill="none", stroke="#8B7355",
        stroke_width=0.4 * PX_PER_MM,
    ))
    # Inner border
    ibpx = (border_mm + 1.5) * PX_PER_MM
    dwg.add(dwg.rect(
        insert=(x + ibpx, y + ibpx),
        size=(cell_w_px - 2 * ibpx, cell_h_px - 2 * ibpx),
        rx=1 * PX_PER_MM, ry=1 * PX_PER_MM,
        fill="none", stroke="#8B7355",
        stroke_width=0.2 * PX_PER_MM,
    ))

    # Optional graphic (some brass plaques may have a small emblem)
    if item.graphic:
        gpath = os.path.join(graphics_dir, item.graphic)
        data_uri = embed_image(gpath)
        if data_uri:
            # Small graphic at top-centre
            gw = cell_w_px * 0.15
            gh = cell_h_px * 0.2
            gx_pos = x + (cell_w_px - gw) / 2
            gy_pos = y + border_mm * PX_PER_MM
            dwg.add(dwg.image(
                href=data_uri,
                insert=(gx_pos, gy_pos),
                size=(gw, gh),
                preserveAspectRatio="xMidYMid meet",
            ))

    center_x = x + cell_w_px * tx

    # Line 1 — heading
    if item.line_1:
        dwg.add(dwg.text(
            str(item.line_1),
            insert=(center_x, y + l1y * PX_PER_MM),
            font_size=f"{l1pt * PT_TO_MM}mm",
            font_family=ff, text_anchor="middle", fill=tf,
        ))

    # Line 2 — name (larger)
    if item.line_2:
        dwg.add(dwg.text(
            str(item.line_2),
            insert=(center_x, y + l2y * PX_PER_MM),
            font_size=f"{l2pt * PT_TO_MM}mm",
            font_family=ff, text_anchor="middle", fill=tf,
            font_weight="bold",
        ))

    # Line 3 — dates/message with word-wrap
    if item.line_3:
        line3_text = str(item.line_3).strip()
        if line3_text:
            lines = []
            for raw in line3_text.split("\n"):
                if raw.strip():
                    lines.extend(split_line_to_fit(raw, max_chars))
            lines = lines[:max_rows]

            text_el = dwg.text(
                "", insert=(center_x, y + l3y * PX_PER_MM),
                font_size=f"{l3pt * PT_TO_MM}mm",
                font_family=ff, text_anchor="middle", fill=tf,
            )
            for i, line in enumerate(lines):
                tspan = dwg.tspan(
                    line.strip(), x=[center_x],
                    dy=["0" if i == 0 else "1.3em"],
                )
                text_el.add(tspan)
            dwg.add(text_el)


class _BrassBase(BaseProcessor):
    """Shared base for brass plaque processors — single-row layout."""
    page_width_mm: float = 480
    corner_radius_mm = 0

    # Subclasses set cell_width_mm and cell_height_mm
    cell_width_mm: float = 150
    cell_height_mm: float = 100

    @property
    def grid_cols(self) -> int:
        return max(1, int(self.page_width_mm // self.cell_width_mm))

    grid_rows: int = 1

    @property
    def page_height_mm(self) -> float:
        return self.cell_height_mm + 4  # small margin

    line1_size_pt = 14.0
    line2_size_pt = 20.0
    line3_size_pt = 10.0


@register("brass_plaque_large")
class BrassPlaqueeLarge(_BrassBase):
    display_name = "Brass Plaque — Large"
    cell_width_mm = 200.0
    cell_height_mm = 150.0


    def render_cell(self, dwg, item, x, y):
        _render_brass_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black",
                           self.layout_overrides)


@register("brass_plaque_medium")
class BrassPlaqueeMedium(_BrassBase):
    display_name = "Brass Plaque — Medium"
    cell_width_mm = 150.0
    cell_height_mm = 100.0

    def render_cell(self, dwg, item, x, y):
        _render_brass_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black",
                           self.layout_overrides)


@register("brass_plaque_small")
class BrassPlaqueeSmall(_BrassBase):
    display_name = "Brass Plaque — Small"
    cell_width_mm = 100.0
    cell_height_mm = 75.0

    def render_cell(self, dwg, item, x, y):
        _render_brass_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black",
                           self.layout_overrides)


@register("laser_engrave_large")
class LaserEngraveLarge(_BrassBase):
    display_name = "Laser Engrave — Large"
    cell_width_mm = 200.0
    cell_height_mm = 150.0

    def render_cell(self, dwg, item, x, y):
        _render_brass_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black",
                           self.layout_overrides)


@register("laser_engrave_medium")
class LaserEngraveMedium(_BrassBase):
    display_name = "Laser Engrave — Medium"
    cell_width_mm = 150.0
    cell_height_mm = 100.0

    def render_cell(self, dwg, item, x, y):
        _render_brass_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black",
                           self.layout_overrides)


@register("laser_engrave_small")
class LaserEngraveSmall(_BrassBase):
    display_name = "Laser Engrave — Small"
    cell_width_mm = 100.0
    cell_height_mm = 75.0

    def render_cell(self, dwg, item, x, y):
        _render_brass_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black",
                           self.layout_overrides)
