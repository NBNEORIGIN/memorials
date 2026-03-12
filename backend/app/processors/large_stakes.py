"""Large Stakes — all 4 variants: graphic coloured, graphic bw, photo coloured, photo bw.

Ported from AmazonPhotoProcessor 2 / coloured_large_stakes.py.
Print sheet: 439.8×289.9 mm, 2×2 grid (4 per page).
Original viewBox: 1662×1095, cell ~755×453 px.
"""

import os
import svgwrite

from app.processors.base import (
    BaseProcessor, OrderItem, PX_PER_MM, PT_TO_MM,
    embed_image, split_line_to_fit,
)
from app.processors.registry import register


def _render_large_graphic_cell(
    dwg, item, x, y, graphics_dir, cell_w_px, cell_h_px,
    line1_pt, line2_pt, line3_pt, text_fill="black",
):
    """Render a large stake graphic cell."""
    if item.graphic:
        gpath = os.path.join(graphics_dir, item.graphic)
        data_uri = embed_image(gpath)
        if data_uri:
            dwg.add(dwg.image(href=data_uri, insert=(x, y),
                              size=(cell_w_px, cell_h_px)))

    center_x = x + cell_w_px / 2
    if item.line_1:
        dwg.add(dwg.text(
            str(item.line_1), insert=(center_x, y + 28 * PX_PER_MM),
            font_size=f"{line1_pt * PT_TO_MM}mm",
            font_family="Georgia", text_anchor="middle", fill=text_fill,
        ))
    if item.line_2:
        dwg.add(dwg.text(
            str(item.line_2), insert=(center_x, y + 50 * PX_PER_MM),
            font_size=f"{line2_pt * PT_TO_MM}mm",
            font_family="Georgia", text_anchor="middle", fill=text_fill,
        ))
    if item.line_3:
        text = str(item.line_3).strip()
        if text:
            lines = split_line_to_fit(text, 50)[:5]
            total = sum(len(l) for l in lines)
            fpt = line1_pt if total <= 30 else (line1_pt * 0.9 if total <= 90 else line3_pt)
            el = dwg.text("", insert=(center_x, y + 68 * PX_PER_MM),
                          font_size=f"{fpt * PT_TO_MM}mm",
                          font_family="Georgia", text_anchor="middle", fill=text_fill)
            for i, ln in enumerate(lines):
                el.add(dwg.tspan(ln.strip(), x=[center_x],
                                 dy=["0" if i == 0 else "1.2em"]))
            dwg.add(el)


def _render_large_photo_cell(
    dwg, item, x, y, graphics_dir, cell_w_px, cell_h_px,
    line1_pt, line2_pt, line3_pt, text_fill="black",
):
    """Render a large stake photo cell (graphic bg + embedded photo)."""
    if item.graphic:
        gpath = os.path.join(graphics_dir, item.graphic)
        data_uri = embed_image(gpath)
        if data_uri:
            dwg.add(dwg.image(href=data_uri, insert=(x, y),
                              size=(cell_w_px, cell_h_px)))
    # Customer photo
    pw, ph = cell_w_px * 0.35, cell_h_px * 0.6
    px, py = x + cell_w_px * 0.05, y + (cell_h_px - ph) / 2
    if item.image_path:
        uri = embed_image(item.image_path)
        if uri:
            dwg.add(dwg.image(href=uri, insert=(px, py), size=(pw, ph),
                              preserveAspectRatio="xMidYMid slice"))

    center_x = x + cell_w_px / 2
    if item.line_1:
        dwg.add(dwg.text(str(item.line_1), insert=(center_x, y + 28 * PX_PER_MM),
                         font_size=f"{line1_pt * PT_TO_MM}mm",
                         font_family="Georgia", text_anchor="middle", fill=text_fill))
    if item.line_2:
        dwg.add(dwg.text(str(item.line_2), insert=(center_x, y + 50 * PX_PER_MM),
                         font_size=f"{line2_pt * PT_TO_MM}mm",
                         font_family="Georgia", text_anchor="middle", fill=text_fill))
    if item.line_3:
        text = str(item.line_3).strip()
        if text:
            lines = split_line_to_fit(text, 50)[:5]
            total = sum(len(l) for l in lines)
            fpt = line1_pt if total <= 30 else (line1_pt * 0.9 if total <= 90 else line3_pt)
            el = dwg.text("", insert=(center_x, y + 68 * PX_PER_MM),
                          font_size=f"{fpt * PT_TO_MM}mm",
                          font_family="Georgia", text_anchor="middle", fill=text_fill)
            for i, ln in enumerate(lines):
                el.add(dwg.tspan(ln.strip(), x=[center_x],
                                 dy=["0" if i == 0 else "1.2em"]))
            dwg.add(el)


# ── Shared layout constants for all large stakes ──────────────────
_LARGE_PAGE_W = 439.8
_LARGE_PAGE_H = 289.9
_LARGE_CELL_W = 200.0    # mm — approximate from original viewBox ratio
_LARGE_CELL_H = 120.0
_LARGE_L1 = 45.33
_LARGE_L2 = 66.67
_LARGE_L3 = 32.0


@register("large_stakes_graphic_coloured")
class LargeStakesGraphicColoured(BaseProcessor):
    display_name = "Large Stake — Coloured Graphic"
    page_width_mm = _LARGE_PAGE_W
    page_height_mm = _LARGE_PAGE_H
    cell_width_mm = _LARGE_CELL_W
    cell_height_mm = _LARGE_CELL_H
    grid_cols = 2
    grid_rows = 2
    line1_size_pt = _LARGE_L1
    line2_size_pt = _LARGE_L2
    line3_size_pt = _LARGE_L3

    def render_cell(self, dwg, item, x, y):
        _render_large_graphic_cell(dwg, item, x, y, self.graphics_dir,
                                   self.cell_width_px, self.cell_height_px,
                                   self.line1_size_pt, self.line2_size_pt,
                                   self.line3_size_pt, "black")


@register("large_stakes_graphic_bw")
class LargeStakesGraphicBW(BaseProcessor):
    display_name = "Large Stake — B&W Graphic"
    page_width_mm = _LARGE_PAGE_W
    page_height_mm = _LARGE_PAGE_H
    cell_width_mm = _LARGE_CELL_W
    cell_height_mm = _LARGE_CELL_H
    grid_cols = 2
    grid_rows = 2
    line1_size_pt = _LARGE_L1
    line2_size_pt = _LARGE_L2
    line3_size_pt = _LARGE_L3

    def render_cell(self, dwg, item, x, y):
        _render_large_graphic_cell(dwg, item, x, y, self.graphics_dir,
                                   self.cell_width_px, self.cell_height_px,
                                   self.line1_size_pt, self.line2_size_pt,
                                   self.line3_size_pt, "black")


@register("large_stakes_photo_coloured")
class LargeStakesPhotoColoured(BaseProcessor):
    display_name = "Large Stake — Coloured Photo"
    page_width_mm = _LARGE_PAGE_W
    page_height_mm = _LARGE_PAGE_H
    cell_width_mm = _LARGE_CELL_W
    cell_height_mm = _LARGE_CELL_H
    grid_cols = 2
    grid_rows = 2
    line1_size_pt = _LARGE_L1
    line2_size_pt = _LARGE_L2
    line3_size_pt = _LARGE_L3

    def render_cell(self, dwg, item, x, y):
        _render_large_photo_cell(dwg, item, x, y, self.graphics_dir,
                                 self.cell_width_px, self.cell_height_px,
                                 self.line1_size_pt, self.line2_size_pt,
                                 self.line3_size_pt, "black")


@register("large_stakes_photo_bw")
class LargeStakesPhotoBW(BaseProcessor):
    display_name = "Large Stake — B&W Photo"
    page_width_mm = _LARGE_PAGE_W
    page_height_mm = _LARGE_PAGE_H
    cell_width_mm = _LARGE_CELL_W
    cell_height_mm = _LARGE_CELL_H
    grid_cols = 2
    grid_rows = 2
    line1_size_pt = _LARGE_L1
    line2_size_pt = _LARGE_L2
    line3_size_pt = _LARGE_L3

    def render_cell(self, dwg, item, x, y):
        _render_large_photo_cell(dwg, item, x, y, self.graphics_dir,
                                 self.cell_width_px, self.cell_height_px,
                                 self.line1_size_pt, self.line2_size_pt,
                                 self.line3_size_pt, "black")
