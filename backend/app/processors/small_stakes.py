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
    text_fill="black",
):
    """Render a small stake cell — graphic + centred text."""
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
    pt_to_mm = PT_TO_MM

    # Line 1 — 3.33pt, 15mm above centre
    if item.line_1:
        lines = split_line_to_fit(str(item.line_1), 30)
        el = dwg.text("", insert=(center_x, center_y - 15 * PX_PER_MM),
                       font_size="3.33pt", font_family="Georgia",
                       text_anchor="middle", fill=text_fill)
        for i, ln in enumerate(lines):
            el.add(dwg.tspan(ln.strip(), x=[center_x],
                             dy=["0" if i == 0 else "1.2em"]))
        dwg.add(el)

    # Line 2 — 2.5mm, centred
    if item.line_2:
        lines = split_line_to_fit(str(item.line_2), 30)
        el = dwg.text("", insert=(center_x, center_y),
                       font_size="2.5mm", font_family="Georgia",
                       text_anchor="middle", fill=text_fill)
        for i, ln in enumerate(lines):
            el.add(dwg.tspan(ln.strip(), x=[center_x],
                             dy=["0" if i == 0 else "1.2em"]))
        dwg.add(el)

    # Line 3 — 3.33pt, 10mm below centre
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
                           self.cell_width_px, self.cell_height_px, "black")


@register("small_stakes_graphic_bw")
class SmallStakesGraphicBW(_SmallStakeBase):
    display_name = "Small Stake — B&W Graphic"

    def render_cell(self, dwg, item, x, y):
        _render_small_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black")
