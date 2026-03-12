"""Regular Stakes — Photo processors (coloured and B&W).

Photo stakes have a photo area instead of a graphic placeholder.
"""

import os
import svgwrite

from app.processors.base import BaseProcessor, OrderItem, ProcessorResult
from app.processors.registry import register


@register("regular_stakes_photo_coloured")
class RegularStakesPhotoColoured(BaseProcessor):
    display_name = "Regular Stake — Coloured Photo"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)

            w_mm, h_mm = 140, 90
            dwg = svgwrite.Drawing(filepath, size=(f"{w_mm}mm", f"{h_mm}mm"), viewBox=f"0 0 {w_mm} {h_mm}")

            dwg.add(dwg.rect(insert=(0, 0), size=(w_mm, h_mm), fill="#f5f0e8"))
            dwg.add(dwg.rect(insert=(2, 2), size=(w_mm - 4, h_mm - 4), fill="none", stroke="#8B7355", stroke_width=0.8))

            # Photo frame (left side)
            photo_x, photo_y, photo_w, photo_h = 5, 8, 45, 55
            dwg.add(dwg.rect(insert=(photo_x, photo_y), size=(photo_w, photo_h), fill="#ddd", stroke="#8B7355", stroke_width=0.5))
            if item.image_path and os.path.exists(item.image_path):
                dwg.add(dwg.image(href=item.image_path, insert=(photo_x, photo_y), size=(photo_w, photo_h), preserveAspectRatio="xMidYMid slice"))
            else:
                dwg.add(dwg.text("PHOTO", insert=(photo_x + photo_w / 2, photo_y + photo_h / 2), text_anchor="middle", dominant_baseline="central", font_size="5", font_family="Arial", fill="#999"))

            # Text lines (right side)
            x_text = 58
            lines = [(item.line_1, 22, "7", "bold"), (item.line_2, 37, "5.5", "normal"), (item.line_3, 49, "5", "italic")]
            for text, y, size, weight in lines:
                if text:
                    dwg.add(dwg.text(text, insert=(x_text, y), text_anchor="start", font_size=size, font_family="Georgia",
                                     font_weight=weight if weight != "italic" else "normal",
                                     font_style="italic" if weight == "italic" else "normal", fill="#333"))

            # Colour bar
            colour_hex = {"Copper": "#B87333", "Gold": "#FFD700", "Silver": "#C0C0C0", "Stone": "#8B8680", "Marble": "#E8E0D8"}.get(item.colour, "#C0C0C0")
            dwg.add(dwg.rect(insert=(0, h_mm - 3), size=(w_mm, 3), fill=colour_hex))

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)
        except Exception as e:
            return ProcessorResult(success=False, error=str(e))


@register("regular_stakes_photo_bw")
class RegularStakesPhotoBW(BaseProcessor):
    display_name = "Regular Stake — B&W Photo"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)

            w_mm, h_mm = 140, 90
            dwg = svgwrite.Drawing(filepath, size=(f"{w_mm}mm", f"{h_mm}mm"), viewBox=f"0 0 {w_mm} {h_mm}")

            dwg.add(dwg.rect(insert=(0, 0), size=(w_mm, h_mm), fill="#1a1a1a"))
            dwg.add(dwg.rect(insert=(2, 2), size=(w_mm - 4, h_mm - 4), fill="none", stroke="#fff", stroke_width=0.8))

            # Photo frame
            photo_x, photo_y, photo_w, photo_h = 5, 8, 45, 55
            dwg.add(dwg.rect(insert=(photo_x, photo_y), size=(photo_w, photo_h), fill="#333", stroke="#666", stroke_width=0.5))
            if item.image_path and os.path.exists(item.image_path):
                dwg.add(dwg.image(href=item.image_path, insert=(photo_x, photo_y), size=(photo_w, photo_h), preserveAspectRatio="xMidYMid slice"))
            else:
                dwg.add(dwg.text("PHOTO", insert=(photo_x + photo_w / 2, photo_y + photo_h / 2), text_anchor="middle", dominant_baseline="central", font_size="5", font_family="Arial", fill="#666"))

            # Text lines
            x_text = 58
            lines = [(item.line_1, 22, "7", "bold"), (item.line_2, 37, "5.5", "normal"), (item.line_3, 49, "5", "italic")]
            for text, y, size, weight in lines:
                if text:
                    dwg.add(dwg.text(text, insert=(x_text, y), text_anchor="start", font_size=size, font_family="Georgia",
                                     font_weight=weight if weight != "italic" else "normal",
                                     font_style="italic" if weight == "italic" else "normal", fill="#fff"))

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)
        except Exception as e:
            return ProcessorResult(success=False, error=str(e))
