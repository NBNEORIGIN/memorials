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
) -> None:
    """Shared cell renderer for photo stakes — graphic + photo + text."""

    # Embed graphic background (full cell)
    if item.graphic:
        gpath = os.path.join(graphics_dir, item.graphic)
        data_uri = embed_image(gpath)
        if data_uri:
            dwg.add(dwg.image(
                href=data_uri, insert=(x, y),
                size=(cell_w_px, cell_h_px),
            ))

    # Embed customer photo (left-centre of cell, ~35% width)
    photo_w = cell_w_px * 0.35
    photo_h = cell_h_px * 0.6
    photo_x = x + cell_w_px * 0.05
    photo_y = y + (cell_h_px - photo_h) / 2
    if item.image_path:
        img_uri = embed_image(item.image_path)
        if img_uri:
            dwg.add(dwg.image(
                href=img_uri, insert=(photo_x, photo_y),
                size=(photo_w, photo_h),
                preserveAspectRatio="xMidYMid slice",
            ))

    center_x = x + cell_w_px / 2

    # Line 1
    if item.line_1:
        dwg.add(dwg.text(
            str(item.line_1),
            insert=(center_x, y + 28 * PX_PER_MM),
            font_size=f"{line1_pt * PT_TO_MM}mm",
            font_family="Georgia", text_anchor="middle", fill=text_fill,
        ))

    # Line 2
    if item.line_2:
        dwg.add(dwg.text(
            str(item.line_2),
            insert=(center_x, y + 45 * PX_PER_MM),
            font_size=f"{line2_pt * PT_TO_MM}mm",
            font_family="Georgia", text_anchor="middle", fill=text_fill,
        ))

    # Line 3 with word-wrap
    if item.line_3:
        line3_text = str(item.line_3).strip()
        if line3_text:
            lines = []
            for raw in line3_text.split("\n"):
                if raw.strip():
                    lines.extend(split_line_to_fit(raw, 40))
            if len(lines) == 1:
                lines = split_line_to_fit(lines[0], 30)
            lines = lines[:5]

            total_chars = sum(len(l) for l in lines)
            if 10 <= total_chars <= 30:
                font_pt = line1_pt
            elif 31 <= total_chars <= 90:
                font_pt = line1_pt * 0.9
            else:
                font_pt = line3_pt

            text_el = dwg.text(
                "", insert=(center_x, y + 57 * PX_PER_MM),
                font_size=f"{font_pt * PT_TO_MM}mm",
                font_family="Georgia", text_anchor="middle", fill=text_fill,
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
            text_fill="black",
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
            text_fill="black",
        )
