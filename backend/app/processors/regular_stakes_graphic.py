"""Regular Stakes — Graphic processors (coloured and B&W).

Ported from AmazonPhotoProcessor 2 / 002 D2C WRITER / regular_stakes.py.
Print sheet: 439.8×289.9 mm, 3×3 grid, cell 140×90 mm (9 per page).
"""

import os
import svgwrite

from app.processors.base import (
    BaseProcessor, OrderItem, PX_PER_MM, PT_TO_MM,
    embed_image, split_line_to_fit,
)
from app.processors.registry import register


def _render_regular_graphic_cell(
    dwg: svgwrite.Drawing, item: OrderItem,
    x: float, y: float, graphics_dir: str,
    cell_w_px: float, cell_h_px: float,
    line1_pt: float, line2_pt: float, line3_pt: float,
    text_fill: str = "black",
    layout: dict | None = None,
) -> None:
    """Shared cell renderer for regular stakes graphic (coloured and BW).

    layout dict can override: line1_y_mm, line2_y_mm, line3_y_mm,
    line1_size_pt, line2_size_pt, line3_size_pt, text_x_frac,
    graphic_x_frac, graphic_y_frac, graphic_w_frac, graphic_h_frac,
    max_chars_line3, line3_max_rows, font_family, text_fill.
    """
    lo = layout or {}
    l1y = lo.get("line1_y_mm", 28.0)
    l2y = lo.get("line2_y_mm", 45.0)
    l3y = lo.get("line3_y_mm", 57.0)
    l1pt = lo.get("line1_size_pt", line1_pt)
    l2pt = lo.get("line2_size_pt", line2_pt)
    l3pt = lo.get("line3_size_pt", line3_pt)
    tx = lo.get("text_x_frac", 0.5)
    ff = lo.get("font_family", "Georgia")
    tf = lo.get("text_fill", text_fill)
    gx = lo.get("graphic_x_frac", 0.0)
    gy = lo.get("graphic_y_frac", 0.0)
    gw = lo.get("graphic_w_frac", 1.0)
    gh = lo.get("graphic_h_frac", 1.0)
    max_chars = lo.get("max_chars_line3", 40)
    max_rows = lo.get("line3_max_rows", 5)

    # Embed graphic
    if item.graphic:
        gpath = os.path.join(graphics_dir, item.graphic)
        data_uri = embed_image(gpath)
        if data_uri:
            dwg.add(dwg.image(
                href=data_uri,
                insert=(x + cell_w_px * gx, y + cell_h_px * gy),
                size=(cell_w_px * gw, cell_h_px * gh),
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

    # Line 2 — name
    if item.line_2:
        dwg.add(dwg.text(
            str(item.line_2),
            insert=(center_x, y + l2y * PX_PER_MM),
            font_size=f"{l2pt * PT_TO_MM}mm",
            font_family=ff, text_anchor="middle", fill=tf,
        ))

    # Line 3 — additional text with word-wrap and adaptive font size
    if item.line_3:
        line3_text = str(item.line_3).strip()
        if line3_text:
            lines = []
            for raw_line in line3_text.split("\n"):
                if raw_line.strip():
                    lines.extend(split_line_to_fit(raw_line, max_chars))
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
                "",
                insert=(center_x, y + l3y * PX_PER_MM),
                font_size=f"{font_pt * PT_TO_MM}mm",
                font_family=ff, text_anchor="middle", fill=tf,
            )
            for i, line in enumerate(lines):
                tspan = dwg.tspan(
                    line.strip(),
                    x=[center_x],
                    dy=["0" if i == 0 else "1.2em"],
                )
                text_el.add(tspan)
            dwg.add(text_el)


@register("regular_stakes_graphic_coloured")
class RegularStakesGraphicColoured(BaseProcessor):
    display_name = "Regular Stake — Coloured Graphic"

    # 3×3 grid on 439.8×289.9mm page, 140×90mm cells
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
        _render_regular_graphic_cell(
            dwg, item, x, y, self.graphics_dir,
            self.cell_width_px, self.cell_height_px,
            self.line1_size_pt, self.line2_size_pt, self.line3_size_pt,
            text_fill="black", layout=self.layout_overrides,
        )


@register("regular_stakes_graphic_bw")
class RegularStakesGraphicBW(BaseProcessor):
    display_name = "Regular Stake — B&W Graphic"

    # BW uses a slightly larger page
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
        _render_regular_graphic_cell(
            dwg, item, x, y, self.graphics_dir,
            self.cell_width_px, self.cell_height_px,
            self.line1_size_pt, self.line2_size_pt, self.line3_size_pt,
            text_fill="black", layout=self.layout_overrides,
        )
