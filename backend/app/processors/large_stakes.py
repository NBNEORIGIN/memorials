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
    line1_pt, line2_pt, line3_pt, text_fill="black", layout=None,
):
    """Render a large stake graphic cell."""
    lo = layout or {}
    l1y = lo.get("line1_y_mm", 28.0)
    l2y = lo.get("line2_y_mm", 50.0)
    l3y = lo.get("line3_y_mm", 68.0)
    l1pt = lo.get("line1_size_pt", line1_pt)
    l2pt = lo.get("line2_size_pt", line2_pt)
    l3pt = lo.get("line3_size_pt", line3_pt)
    tx = lo.get("text_x_frac", 0.5)
    ff = lo.get("font_family", "Georgia")
    tf = lo.get("text_fill", text_fill)
    max_chars = lo.get("max_chars_line3", 50)
    max_rows = lo.get("line3_max_rows", 5)

    if item.graphic:
        gpath = os.path.join(graphics_dir, item.graphic)
        data_uri = embed_image(gpath)
        if data_uri:
            dwg.add(dwg.image(href=data_uri, insert=(x, y),
                              size=(cell_w_px, cell_h_px)))

    center_x = x + cell_w_px * tx
    if item.line_1:
        dwg.add(dwg.text(
            str(item.line_1), insert=(center_x, y + l1y * PX_PER_MM),
            font_size=f"{l1pt * PT_TO_MM}mm",
            font_family=ff, text_anchor="middle", fill=tf,
        ))
    if item.line_2:
        dwg.add(dwg.text(
            str(item.line_2), insert=(center_x, y + l2y * PX_PER_MM),
            font_size=f"{l2pt * PT_TO_MM}mm",
            font_family=ff, text_anchor="middle", fill=tf,
        ))
    if item.line_3:
        text = str(item.line_3).strip()
        if text:
            lines = split_line_to_fit(text, max_chars)[:max_rows]
            total = sum(len(l) for l in lines)
            fpt = l1pt if total <= 30 else (l1pt * 0.9 if total <= 90 else l3pt)
            el = dwg.text("", insert=(center_x, y + l3y * PX_PER_MM),
                          font_size=f"{fpt * PT_TO_MM}mm",
                          font_family=ff, text_anchor="middle", fill=tf)
            for i, ln in enumerate(lines):
                el.add(dwg.tspan(ln.strip(), x=[center_x],
                                 dy=["0" if i == 0 else "1.2em"]))
            dwg.add(el)


def _render_large_photo_cell(
    dwg, item, x, y, graphics_dir, cell_w_px, cell_h_px,
    line1_pt, line2_pt, line3_pt, text_fill="black", layout=None,
):
    """Render a large stake photo cell (graphic bg + embedded photo)."""
    lo = layout or {}
    l1y = lo.get("line1_y_mm", 28.0)
    l2y = lo.get("line2_y_mm", 50.0)
    l3y = lo.get("line3_y_mm", 68.0)
    l1pt = lo.get("line1_size_pt", line1_pt)
    l2pt = lo.get("line2_size_pt", line2_pt)
    l3pt = lo.get("line3_size_pt", line3_pt)
    # Default text X shifted right (0.65) to avoid overlapping the photo area
    tx = lo.get("text_x_frac", 0.65)
    ff = lo.get("font_family", "Georgia")
    tf = lo.get("text_fill", text_fill)
    px_frac = lo.get("photo_x_frac", 0.05)
    pw_frac = lo.get("photo_w_frac", 0.35)
    ph_frac = lo.get("photo_h_frac", 0.6)
    max_chars = lo.get("max_chars_line3", 50)
    max_rows = lo.get("line3_max_rows", 5)

    if item.graphic:
        gpath = os.path.join(graphics_dir, item.graphic)
        data_uri = embed_image(gpath)
        if data_uri:
            dwg.add(dwg.image(href=data_uri, insert=(x, y),
                              size=(cell_w_px, cell_h_px)))
    # Customer photo — vertically centred with clip path
    pw, ph = cell_w_px * pw_frac, cell_h_px * ph_frac
    ppx = x + cell_w_px * px_frac
    ppy = y + (cell_h_px - ph) / 2  # true vertical centre
    if item.image_path:
        uri = embed_image(item.image_path)
        if uri:
            clip_id = f"photo-clip-{id(item)}-{int(x)}-{int(y)}"
            clip = dwg.defs.add(dwg.clipPath(id=clip_id))
            clip.add(dwg.rect(insert=(ppx, ppy), size=(pw, ph),
                              rx=2 * PX_PER_MM, ry=2 * PX_PER_MM))
            dwg.add(dwg.image(href=uri, insert=(ppx, ppy), size=(pw, ph),
                              preserveAspectRatio="xMidYMid slice",
                              clip_path=f"url(#{clip_id})"))

    center_x = x + cell_w_px * tx
    if item.line_1:
        dwg.add(dwg.text(str(item.line_1), insert=(center_x, y + l1y * PX_PER_MM),
                         font_size=f"{l1pt * PT_TO_MM}mm",
                         font_family=ff, text_anchor="middle", fill=tf))
    if item.line_2:
        dwg.add(dwg.text(str(item.line_2), insert=(center_x, y + l2y * PX_PER_MM),
                         font_size=f"{l2pt * PT_TO_MM}mm",
                         font_family=ff, text_anchor="middle", fill=tf))
    if item.line_3:
        text = str(item.line_3).strip()
        if text:
            lines = split_line_to_fit(text, max_chars)[:max_rows]
            total = sum(len(l) for l in lines)
            fpt = l1pt if total <= 30 else (l1pt * 0.9 if total <= 90 else l3pt)
            el = dwg.text("", insert=(center_x, y + l3y * PX_PER_MM),
                          font_size=f"{fpt * PT_TO_MM}mm",
                          font_family=ff, text_anchor="middle", fill=tf)
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
                                   self.line3_size_pt, "black", self.layout_overrides)


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
                                   self.line3_size_pt, "black", self.layout_overrides)


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
                                 self.line3_size_pt, "black", self.layout_overrides)


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
                                 self.line3_size_pt, "black", self.layout_overrides)
