"""Regular Stakes — Photo processors (coloured and B&W).

Photo stakes embed a customer photo alongside text.
Same grid layout as graphic stakes: 3×3 on 439.8×289.9mm (coloured) or 480×330mm (BW).

Smart text layout: text is constrained to the zone right of the photo,
with dynamic font sizing and word-wrap that respects intentional newlines.
"""

import os
import svgwrite

from app.processors.base import (
    BaseProcessor, OrderItem, PX_PER_MM, PT_TO_MM,
    embed_image, split_line_to_fit, smart_wrap_text,
)
from app.processors.registry import register

# Photo border radius in mm (black rounded border around customer photo)
PHOTO_BORDER_RADIUS_MM = 6.0
PHOTO_BORDER_STROKE_MM = 1.2


def _render_photo_cell(
    dwg: svgwrite.Drawing, item: OrderItem,
    x: float, y: float, graphics_dir: str,
    cell_w_px: float, cell_h_px: float,
    line1_pt: float, line2_pt: float, line3_pt: float,
    text_fill: str = "black",
    layout: dict | None = None,
) -> None:
    """Shared cell renderer for photo stakes — graphic + photo + text.

    Text is positioned in the zone to the right of the photo.
    Font size adapts dynamically so text never overlaps the photo.
    Customer newlines (poems, dates) are preserved.
    """
    lo = layout or {}
    cell_w_mm = cell_w_px / PX_PER_MM
    cell_h_mm = cell_h_px / PX_PER_MM

    # Layout values
    l1y = lo.get("line1_y_mm", cell_h_mm * 0.22)
    l2y = lo.get("line2_y_mm", cell_h_mm * 0.42)
    l3y = lo.get("line3_y_mm", cell_h_mm * 0.60)
    l1pt = lo.get("line1_size_pt", line1_pt)
    l2pt = lo.get("line2_size_pt", line2_pt)
    l3pt = lo.get("line3_size_pt", line3_pt)
    ff = lo.get("font_family", "Georgia")
    tf = lo.get("text_fill", text_fill)
    gx = lo.get("graphic_x_frac", 0.0)
    gy = lo.get("graphic_y_frac", 0.0)
    gw = lo.get("graphic_w_frac", 1.0)
    gh = lo.get("graphic_h_frac", 1.0)
    px_frac = lo.get("photo_x_frac", 0.05)
    pw_frac = lo.get("photo_w_frac", 0.35)
    ph_frac = lo.get("photo_h_frac", 0.6)
    max_rows = lo.get("line3_max_rows", 6)
    border_r_mm = lo.get("photo_border_radius_mm", PHOTO_BORDER_RADIUS_MM)

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

    # ── Photo placement ──
    photo_w = cell_w_px * pw_frac
    photo_h = cell_h_px * ph_frac
    photo_x = x + cell_w_px * px_frac
    photo_y = y + (cell_h_px - photo_h) / 2

    has_photo = False
    if item.image_path:
        img_uri = embed_image(item.image_path)
        if img_uri:
            has_photo = True
            clip_id = f"photo-clip-{id(item)}-{int(x)}-{int(y)}"
            clip = dwg.defs.add(dwg.clipPath(id=clip_id))
            clip.add(dwg.rect(
                insert=(photo_x, photo_y),
                size=(photo_w, photo_h),
                rx=border_r_mm * PX_PER_MM,
                ry=border_r_mm * PX_PER_MM,
            ))
            dwg.add(dwg.image(
                href=img_uri, insert=(photo_x, photo_y),
                size=(photo_w, photo_h),
                preserveAspectRatio="xMidYMin slice",
                clip_path=f"url(#{clip_id})",
            ))
            # Black border around photo
            dwg.add(dwg.rect(
                insert=(photo_x, photo_y),
                size=(photo_w, photo_h),
                rx=border_r_mm * PX_PER_MM,
                ry=border_r_mm * PX_PER_MM,
                fill="none", stroke="black",
                stroke_width=PHOTO_BORDER_STROKE_MM * PX_PER_MM,
            ))

    # ── Text zone calculation ──
    # Text is constrained to the area right of the photo
    if has_photo:
        photo_right_mm = (px_frac + pw_frac) * cell_w_mm
        text_gap_mm = 3.0  # gap between photo and text
        text_left_mm = photo_right_mm + text_gap_mm
        text_right_mm = cell_w_mm - 2.0  # small right margin
        text_zone_width_mm = text_right_mm - text_left_mm
        text_center_x = x + ((text_left_mm + text_right_mm) / 2) * PX_PER_MM
    else:
        # No photo — centre text in cell
        text_zone_width_mm = cell_w_mm * 0.85
        text_center_x = x + cell_w_px * 0.5

    # ── Line 1 — heading ──
    if item.line_1:
        line1_text = str(item.line_1)
        # Smart-wrap line 1 within text zone
        l1_lines, l1_final_pt = smart_wrap_text(
            line1_text, text_zone_width_mm, l1pt,
            max_rows=2, min_font_pt=10.0, shrink_step_pt=1.0,
        )
        if l1_lines:
            el = dwg.text(
                "", insert=(text_center_x, y + l1y * PX_PER_MM),
                font_size=f"{l1_final_pt * PT_TO_MM}mm",
                font_family=ff, text_anchor="middle", fill=tf,
            )
            for i, ln in enumerate(l1_lines):
                el.add(dwg.tspan(ln.strip(), x=[text_center_x],
                                 dy=["0" if i == 0 else "1.2em"]))
            dwg.add(el)

    # ── Line 2 — name (larger) ──
    if item.line_2:
        line2_text = str(item.line_2)
        l2_lines, l2_final_pt = smart_wrap_text(
            line2_text, text_zone_width_mm, l2pt,
            max_rows=2, min_font_pt=12.0, shrink_step_pt=1.5,
        )
        if l2_lines:
            el = dwg.text(
                "", insert=(text_center_x, y + l2y * PX_PER_MM),
                font_size=f"{l2_final_pt * PT_TO_MM}mm",
                font_family=ff, text_anchor="middle", fill=tf,
            )
            for i, ln in enumerate(l2_lines):
                el.add(dwg.tspan(ln.strip(), x=[text_center_x],
                                 dy=["0" if i == 0 else "1.2em"]))
            dwg.add(el)

    # ── Line 3 — additional text with smart wrapping ──
    if item.line_3:
        line3_text = str(item.line_3).strip()
        if line3_text:
            l3_lines, l3_final_pt = smart_wrap_text(
                line3_text, text_zone_width_mm, l3pt,
                max_rows=max_rows, min_font_pt=8.0, shrink_step_pt=0.5,
            )
            if l3_lines:
                el = dwg.text(
                    "", insert=(text_center_x, y + l3y * PX_PER_MM),
                    font_size=f"{l3_final_pt * PT_TO_MM}mm",
                    font_family=ff, text_anchor="middle", fill=tf,
                )
                for i, ln in enumerate(l3_lines):
                    el.add(dwg.tspan(ln.strip(), x=[text_center_x],
                                     dy=["0" if i == 0 else "1.2em"]))
                dwg.add(el)


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
            text_fill="black", layout=item.layout_overrides or self.layout_overrides,
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
            text_fill="black", layout=item.layout_overrides or self.layout_overrides,
        )
