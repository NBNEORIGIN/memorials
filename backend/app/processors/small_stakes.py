"""Small Stakes — graphic coloured and graphic B&W.

Ported from AmazonPhotoProcessor 2 / coloured_small_stakes_template_processor.py.
Print sheet: 480×290 mm, 3×3 grid, cell 108×75 mm (9 per page).
Grid is bottom-right aligned on the page.
"""

import os
import svgwrite

from app.processors.base import (
    BaseProcessor, OrderItem, PX_PER_MM, PT_TO_MM,
    embed_image, split_line_to_fit,
)
from app.processors.registry import register


def _render_small_cell(
    dwg, item, x, y, graphics_dir, cell_w_px, cell_h_px,
    text_fill="black", layout=None,
):
    """Render a small stake cell — graphic + centred text.

    Font sizes in pt, converted to mm for SVG.
    Small stakes cell is 108×75mm — text must be readable.
    """
    lo = layout or {}
    cell_w_mm = cell_w_px / PX_PER_MM
    cell_h_mm = cell_h_px / PX_PER_MM
    l1y = lo.get("line1_y_mm", cell_h_mm * 0.28)
    l2y = lo.get("line2_y_mm", cell_h_mm * 0.50)
    l3y = lo.get("line3_y_mm", cell_h_mm * 0.68)
    # Proper pt sizes — readable on 108×75mm cell
    l1pt = lo.get("line1_size_pt", 24.0)
    l2pt = lo.get("line2_size_pt", 32.0)
    l3pt = lo.get("line3_size_pt", 18.0)
    tx = lo.get("text_x_frac", 0.5)
    ff = lo.get("font_family", "Georgia")
    tf = lo.get("text_fill", text_fill)
    max_chars = lo.get("max_chars_line3", 25)
    max_rows = lo.get("line3_max_rows", 4)

    if item.graphic:
        gpath = os.path.join(graphics_dir, item.graphic)
        data_uri = embed_image(gpath)
        if data_uri:
            dwg.add(dwg.image(
                href=data_uri, insert=(x, y),
                size=(cell_w_px, cell_h_px),
                preserveAspectRatio="xMidYMid meet",
            ))

    center_x = x + cell_w_px * tx

    # Line 1 — heading
    if item.line_1:
        lines = split_line_to_fit(str(item.line_1), max_chars)
        el = dwg.text("", insert=(center_x, y + l1y * PX_PER_MM),
                       font_size=f"{l1pt * PT_TO_MM}mm", font_family=ff,
                       text_anchor="middle", fill=tf)
        for i, ln in enumerate(lines):
            el.add(dwg.tspan(ln.strip(), x=[center_x],
                             dy=["0" if i == 0 else "1.2em"]))
        dwg.add(el)

    # Line 2 — name (larger)
    if item.line_2:
        lines = split_line_to_fit(str(item.line_2), max_chars)
        el = dwg.text("", insert=(center_x, y + l2y * PX_PER_MM),
                       font_size=f"{l2pt * PT_TO_MM}mm", font_family=ff,
                       text_anchor="middle", fill=tf)
        for i, ln in enumerate(lines):
            el.add(dwg.tspan(ln.strip(), x=[center_x],
                             dy=["0" if i == 0 else "1.2em"]))
        dwg.add(el)

    # Line 3 — additional text
    if item.line_3:
        lines = split_line_to_fit(str(item.line_3), max_chars)[:max_rows]
        if lines:
            el = dwg.text("", insert=(center_x, y + l3y * PX_PER_MM),
                           font_size=f"{l3pt * PT_TO_MM}mm", font_family=ff,
                           text_anchor="middle", fill=tf)
            for i, ln in enumerate(lines):
                el.add(dwg.tspan(ln.strip(), x=[center_x],
                                 dy=["0" if i == 0 else "1.2em"]))
            dwg.add(el)


class _SmallStakeBase(BaseProcessor):
    """Shared layout for small stakes — 480×290 mm page, 108×75 mm cells, 3×3 grid."""
    page_width_mm = 480
    page_height_mm = 290
    cell_width_mm = 108
    cell_height_mm = 75
    grid_cols = 3
    grid_rows = 3
    corner_radius_mm = 6

    @property
    def x_offset_px(self):
        """Bottom-right aligned: grid flush to right edge."""
        grid_w = self.cell_width_mm * self.grid_cols
        return (self.page_width_mm - grid_w) * PX_PER_MM

    @property
    def y_offset_px(self):
        """Bottom-right aligned: grid flush to bottom edge."""
        grid_h = self.cell_height_mm * self.grid_rows
        return (self.page_height_mm - grid_h) * PX_PER_MM


@register("small_stakes_graphic_coloured")
class SmallStakesGraphicColoured(_SmallStakeBase):
    display_name = "Small Stake — Coloured Graphic"

    def render_cell(self, dwg, item, x, y):
        _render_small_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black",
                           item.layout_overrides or self.layout_overrides)


@register("small_stakes_graphic_bw")
class SmallStakesGraphicBW(_SmallStakeBase):
    display_name = "Small Stake — B&W Graphic"

    def render_cell(self, dwg, item, x, y):
        _render_small_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black",
                           item.layout_overrides or self.layout_overrides)
