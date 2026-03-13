"""Heart Stakes — graphic coloured and generic graphic.

Ported from AmazonPhotoProcessor 2 / coloured_heart_stakes_processor.py.
Print sheet: 480×330 mm, 3×1 grid, cell ~140×90 mm (3 per page).
Grid is bottom-right aligned. Heart outline drawn via SVG path.
"""

import os
import svgwrite

from app.processors.base import (
    BaseProcessor, OrderItem, PX_PER_MM, PT_TO_MM,
    embed_image, split_line_to_fit,
)
from app.processors.registry import register

# Heart path data — extracted from the original SVG template.
# Coordinates are relative to the cell's (0,0) origin.
_HEART_PATH_D = (
    "m 39.30,-15.59 c -2.42,-0.01 -4.84,0.24 -7.38,0.74 "
    "-11.86,2.35 -22.32,10.42 -27.87,21.47 "
    "-3.85,7.67 -4.89,15.61 -3.36,25.68 "
    "1.97,13.00 8.70,24.41 21.43,36.39 "
    "16.66,16.61 44.49,45.62 47.66,45.62 h 0.36 "
    "c 3.17,0 31.01,-29.01 47.66,-45.62 "
    "12.74,-11.98 19.46,-23.39 21.43,-36.39 "
    "1.53,-10.07 0.49,-18.01 -3.36,-25.68 "
    "-5.55,-11.06 -16.02,-19.12 -27.87,-21.47 "
    "-2.54,-0.50 -4.96,-0.75 -7.38,-0.74 "
    "-3.11,0.02 -6.23,0.46 -9.60,1.35 "
    "-7.55,1.99 -15.04,6.73 -20.08,12.72 "
    "-0.38,0.45 -0.72,0.84 -0.98,1.13 "
    "-0.26,-0.29 -0.60,-0.68 -0.98,-1.13 "
    "-5.04,-5.99 -12.53,-10.73 -20.08,-12.72 "
    "-3.37,-0.89 -6.49,-1.33 -9.60,-1.35 z"
)


def _render_heart_cell(
    dwg, item, x, y, graphics_dir, cell_w_px, cell_h_px,
    text_fill="black", layout=None,
):
    """Render a heart stake cell with heart outline, graphic, and text."""
    lo = layout or {}
    cell_h_mm = cell_h_px / PX_PER_MM
    l1y = lo.get("line1_y_mm", cell_h_mm / 2 - 10)
    l2y = lo.get("line2_y_mm", cell_h_mm / 2 + 3)
    l3y = lo.get("line3_y_mm", cell_h_mm / 2 + 15)
    tx = lo.get("text_x_frac", 0.5)
    ff = lo.get("font_family", "Georgia")
    tf = lo.get("text_fill", text_fill)
    max_chars = lo.get("max_chars_line3", 30)
    max_rows = lo.get("line3_max_rows", 5)

    # Embed graphic background
    if item.graphic:
        gpath = os.path.join(graphics_dir, item.graphic)
        data_uri = embed_image(gpath)
        if data_uri:
            dwg.add(dwg.image(
                href=data_uri, insert=(x, y),
                size=(cell_w_px, cell_h_px),
                preserveAspectRatio="xMidYMid meet",
            ))

    # Draw heart outline
    heart_group = dwg.g(transform=f"translate({x + cell_w_px * 0.01},{y + cell_h_px * 0.17})")
    scale_x = cell_w_px / (140 * PX_PER_MM)
    scale_y = cell_h_px / (90 * PX_PER_MM)
    scale = min(scale_x, scale_y)
    heart_group.add(dwg.path(
        d=_HEART_PATH_D,
        transform=f"scale({scale})",
        fill="none", stroke="red",
        stroke_width=0.5 / scale,
    ))
    dwg.add(heart_group)

    center_x = x + cell_w_px * tx

    # Text lines
    if item.line_1:
        lines = split_line_to_fit(str(item.line_1), max_chars)
        el = dwg.text("", insert=(center_x, y + l1y * PX_PER_MM),
                       font_size="3.33pt", font_family=ff,
                       text_anchor="middle", fill=tf)
        for i, ln in enumerate(lines):
            el.add(dwg.tspan(ln.strip(), x=[center_x],
                             dy=["0" if i == 0 else "1.2em"]))
        dwg.add(el)

    if item.line_2:
        lines = split_line_to_fit(str(item.line_2), max_chars)
        el = dwg.text("", insert=(center_x, y + l2y * PX_PER_MM),
                       font_size="2.5mm", font_family=ff,
                       text_anchor="middle", fill=tf)
        for i, ln in enumerate(lines):
            el.add(dwg.tspan(ln.strip(), x=[center_x],
                             dy=["0" if i == 0 else "1.2em"]))
        dwg.add(el)

    if item.line_3:
        lines = split_line_to_fit(str(item.line_3), max_chars)[:max_rows]
        if lines:
            el = dwg.text("", insert=(center_x, y + l3y * PX_PER_MM),
                           font_size="3.33pt", font_family=ff,
                           text_anchor="middle", fill=tf)
            for i, ln in enumerate(lines):
                el.add(dwg.tspan(ln.strip(), x=[center_x],
                                 dy=["0" if i == 0 else "1.2em"]))
            dwg.add(el)


class _HeartStakeBase(BaseProcessor):
    """Shared layout: 480×330mm page, 3×1 grid (3 per page), cell ~140×90 mm."""
    page_width_mm = 480
    page_height_mm = 330
    cell_width_mm = 139.913
    cell_height_mm = 89.826
    grid_cols = 3
    grid_rows = 1
    corner_radius_mm = 0   # heart shape, not rounded rect

    @property
    def x_offset_px(self):
        grid_w = self.cell_width_mm * self.grid_cols
        return (self.page_width_mm - grid_w - 1.0) * PX_PER_MM

    @property
    def y_offset_px(self):
        grid_h = self.cell_height_mm * self.grid_rows
        return (self.page_height_mm - grid_h - 1.0) * PX_PER_MM


@register("heart_stakes_graphic_coloured")
class HeartStakesGraphicColoured(_HeartStakeBase):
    display_name = "Heart Stake — Coloured Graphic"

    def render_cell(self, dwg, item, x, y):
        _render_heart_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black",
                           self.layout_overrides)


@register("heart_stakes_graphic")
class HeartStakesGraphic(_HeartStakeBase):
    display_name = "Heart Stake — Graphic"

    def render_cell(self, dwg, item, x, y):
        _render_heart_cell(dwg, item, x, y, self.graphics_dir,
                           self.cell_width_px, self.cell_height_px, "black",
                           self.layout_overrides)
