"""Metal processors — Large, XL, Medium, Small metal graphic stakes.

Ported from AmazonPhotoProcessor 2 / base_metal_processor.py + size subclasses.
Metal plaques use a single-row layout on a 480mm-wide page.
batch_size = page_width // cell_width (items in one row).
Exact dimensions from original:
  Large:  127  × 76.2 mm → 3 per row
  XL:     152.4 × 101.6 mm → 3 per row
  Medium: 101.6 × 50.8 mm → 4 per row
  Small:   76.2 × 38.1 mm → 6 per row
"""

import os
import svgwrite

from app.processors.base import (
    BaseProcessor, OrderItem, PX_PER_MM, PT_TO_MM,
    embed_image, split_line_to_fit,
)
from app.processors.registry import register


def _render_metal_cell(
    dwg, item, x, y, graphics_dir, cell_w_px, cell_h_px,
    text_fill="black",
):
    """Render a metal plaque cell — graphic + centred text."""
    if item.graphic:
        gpath = os.path.join(graphics_dir, item.graphic)
        data_uri = embed_image(gpath)
        if data_uri:
            dwg.add(dwg.image(
                href=data_uri, insert=(x, y),
                size=(cell_w_px, cell_h_px),
                preserveAspectRatio="xMidYMid meet",
            ))

    center_x = x + cell_w_px / 2
    center_y = y + cell_h_px / 2

    # Line 1 — heading
    if item.line_1:
        lines = split_line_to_fit(str(item.line_1), 30)
        el = dwg.text("", insert=(center_x, center_y - 12 * PX_PER_MM),
                       font_size="3.33pt", font_family="Georgia",
                       text_anchor="middle", fill=text_fill)
        for i, ln in enumerate(lines):
            el.add(dwg.tspan(ln.strip(), x=[center_x],
                             dy=["0" if i == 0 else "1.2em"]))
        dwg.add(el)

    # Line 2 — name
    if item.line_2:
        lines = split_line_to_fit(str(item.line_2), 30)
        el = dwg.text("", insert=(center_x, center_y),
                       font_size="2.5mm", font_family="Georgia",
                       text_anchor="middle", fill=text_fill)
        for i, ln in enumerate(lines):
            el.add(dwg.tspan(ln.strip(), x=[center_x],
                             dy=["0" if i == 0 else "1.2em"]))
        dwg.add(el)

    # Line 3 — additional text
    if item.line_3:
        lines = split_line_to_fit(str(item.line_3), 30)[:5]
        if lines:
            el = dwg.text("", insert=(center_x, center_y + 10 * PX_PER_MM),
                           font_size="3.33pt", font_family="Georgia",
                           text_anchor="middle", fill=text_fill)
            for i, ln in enumerate(lines):
                el.add(dwg.tspan(ln.strip(), x=[center_x],
                                 dy=["0" if i == 0 else "1.2em"]))
            dwg.add(el)


class _MetalBase(BaseProcessor):
    """Shared base for metal plaques — 480mm wide page, single-row layout."""
    page_width_mm: float = 480
    corner_radius_mm = 0
    grid_rows = 1

    @property
    def page_height_mm(self):
        return self.cell_height_mm + 2   # tight fit — 1mm margin each side

    @property
    def grid_cols(self):
        return int(self.page_width_mm // self.cell_width_mm)

    @property
    def x_offset_px(self):
        """Centre the row of items on the page."""
        used = self.cell_width_mm * self.grid_cols
        return ((self.page_width_mm - used) / 2) * PX_PER_MM

    @property
    def y_offset_px(self):
        return 1.0 * PX_PER_MM   # 1mm top margin


@register("large_metal_graphic")
class LargeMetalGraphic(_MetalBase):
    display_name = "Large Metal — Graphic"
    cell_width_mm = 127.0
    cell_height_mm = 76.2

    def render_cell(self, dwg, item, x, y):
        _render_metal_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black")


@register("xl_metal_graphic")
class XLMetalGraphic(_MetalBase):
    display_name = "XL Metal — Graphic"
    cell_width_mm = 152.4
    cell_height_mm = 101.6

    def render_cell(self, dwg, item, x, y):
        _render_metal_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black")


@register("medium_metal_graphic")
class MediumMetalGraphic(_MetalBase):
    display_name = "Medium Metal — Graphic"
    cell_width_mm = 101.6
    cell_height_mm = 50.8

    def render_cell(self, dwg, item, x, y):
        _render_metal_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black")


@register("small_metal_graphic")
class SmallMetalGraphic(_MetalBase):
    display_name = "Small Metal — Graphic"
    cell_width_mm = 76.2
    cell_height_mm = 38.1

    def render_cell(self, dwg, item, x, y):
        _render_metal_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black")
