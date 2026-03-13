"""Regular Stakes — Photo processors (coloured and B&W).

Photo stakes embed a customer photo alongside text.
Same grid layout as graphic stakes: 3×3 on 439.8×289.9mm (coloured) or 480×330mm (BW).
"""

import os
import svgwrite

from app.processors.base import (
    BaseProcessor, OrderItem, PX_PER_MM, PT_TO_MM,
    embed_image, split_line_to_fit,
)
from app.processors.registry import register


def _render_photo_cell(
    dwg: svgwrite.Drawing, item: OrderItem,
    x: float, y: float, graphics_dir: str,
    cell_w_px: float, cell_h_px: float,
    line1_pt: float, line2_pt: float, line3_pt: float,
    text_fill: str = "black",
    layout: dict | None = None,
) -> None:
    """Shared cell renderer for photo stakes — graphic + photo + text."""
    lo = layout or {}
    l1y = lo.get("line1_y_mm", 28.0)
    l2y = lo.get("line2_y_mm", 45.0)
    l3y = lo.get("line3_y_mm", 57.0)
    l1pt = lo.get("line1_size_pt", line1_pt)
    l2pt = lo.get("line2_size_pt", line2_pt)
    l3pt = lo.get("line3_size_pt", line3_pt)
    # Default text X shifted right (0.65) to avoid overlapping the photo area
    tx = lo.get("text_x_frac", 0.65)
    ff = lo.get("font_family", "Georgia")
    tf = lo.get("text_fill", text_fill)
    gx = lo.get("graphic_x_frac", 0.0)
    gy = lo.get("graphic_y_frac", 0.0)
    gw = lo.get("graphic_w_frac", 1.0)
    gh = lo.get("graphic_h_frac", 1.0)
    px_frac = lo.get("photo_x_frac", 0.05)
    pw_frac = lo.get("photo_w_frac", 0.35)
    ph_frac = lo.get("photo_h_frac", 0.6)
    max_chars = lo.get("max_chars_line3", 40)
    max_rows = lo.get("line3_max_rows", 5)

    # Embed graphic background
    if item.graphic:
        gpath = os.path.join(graphics_dir, item.graphic)
        data_uri = embed_image(gpath)
        if data_uri:
            dwg.add(dwg.image(
                href=data_uri,
                insert=(x + cell_w_px * gx, y + cell_h_px * gy),
                size=(cell_w_px * gw, cell_h_px * gh),
            ))

    # Embed customer photo — vertically centred within cell
    photo_w = cell_w_px * pw_frac
    photo_h = cell_h_px * ph_frac
    photo_x = x + cell_w_px * px_frac
    photo_y = y + (cell_h_px - photo_h) / 2  # true vertical centre
    if item.image_path:
        img_uri = embed_image(item.image_path)
        if img_uri:
            # Create clip path for clean photo cropping
            clip_id = f"photo-clip-{id(item)}-{int(x)}-{int(y)}"
            clip = dwg.defs.add(dwg.clipPath(id=clip_id))
            clip.add(dwg.rect(
                insert=(photo_x, photo_y),
                size=(photo_w, photo_h),
                rx=2 * PX_PER_MM, ry=2 * PX_PER_MM,
            ))
            dwg.add(dwg.image(
                href=img_uri, insert=(photo_x, photo_y),
                size=(photo_w, photo_h),
                preserveAspectRatio="xMidYMid slice",
                clip_path=f"url(#{clip_id})",
            ))

    center_x = x + cell_w_px * tx

    # Line 1
    if item.line_1:
        dwg.add(dwg.text(
            str(item.line_1),
            insert=(center_x, y + l1y * PX_PER_MM),
            font_size=f"{l1pt * PT_TO_MM}mm",
            font_family=ff, text_anchor="middle", fill=tf,
        ))

    # Line 2
    if item.line_2:
        dwg.add(dwg.text(
            str(item.line_2),
            insert=(center_x, y + l2y * PX_PER_MM),
            font_size=f"{l2pt * PT_TO_MM}mm",
            font_family=ff, text_anchor="middle", fill=tf,
        ))

    # Line 3 with word-wrap
    if item.line_3:
        line3_text = str(item.line_3).strip()
        if line3_text:
            lines = []
            for raw in line3_text.split("\n"):
                if raw.strip():
                    lines.extend(split_line_to_fit(raw, max_chars))
            if len(lines) == 1:
                lines = split_line_to_fit(lines[0], max(max_chars - 10, 20))
            lines = lines[:max_rows]

            total_chars = sum(len(l) for l in lines)
            if 10 <= total_chars <= 30:
                font_pt = l1pt
            elif 31 <= total_chars <= 90:
                font_pt = l1pt * 0.9
            else:
                font_pt = l3pt

            text_el = dwg.text(
                "", insert=(center_x, y + l3y * PX_PER_MM),
                font_size=f"{font_pt * PT_TO_MM}mm",
                font_family=ff, text_anchor="middle", fill=tf,
            )
            for i, line in enumerate(lines):
                tspan = dwg.tspan(line.strip(), x=[center_x],
                                  dy=["0" if i == 0 else "1.2em"])
                text_el.add(tspan)
            dwg.add(text_el)


@register("regular_stakes_photo_coloured")
class RegularStakesPhotoColoured(BaseProcessor):
    display_name = "Regular Stake — Coloured Photo"

    page_width_mm = 439.8
    page_height_mm = 289.9
    cell_width_mm = 140
    cell_height_mm = 90
    grid_cols = 3
    grid_rows = 3

    line1_size_pt = 17 * 1.2
    line2_size_pt = 25 * 1.2
    line3_size_pt = 12 * 1.1

    def render_cell(self, dwg, item, x, y):
        _render_photo_cell(
            dwg, item, x, y, self.graphics_dir,
            self.cell_width_px, self.cell_height_px,
            self.line1_size_pt, self.line2_size_pt, self.line3_size_pt,
            text_fill="black", layout=self.layout_overrides,
        )


@register("regular_stakes_photo_bw")
class RegularStakesPhotoBW(BaseProcessor):
    display_name = "Regular Stake — B&W Photo"

    page_width_mm = 480
    page_height_mm = 330
    cell_width_mm = 140
    cell_height_mm = 90
    grid_cols = 3
    grid_rows = 3

    line1_size_pt = 17 * 1.2
    line2_size_pt = 25 * 1.2
    line3_size_pt = 12 * 1.1

    def render_cell(self, dwg, item, x, y):
        _render_photo_cell(
            dwg, item, x, y, self.graphics_dir,
            self.cell_width_px, self.cell_height_px,
            self.line1_size_pt, self.line2_size_pt, self.line3_size_pt,
            text_fill="black", layout=self.layout_overrides,
        )
