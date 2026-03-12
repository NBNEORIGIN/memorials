"""Large Stakes — all 4 variants: graphic coloured, graphic bw, photo coloured, photo bw."""

import os
import svgwrite

from app.processors.base import BaseProcessor, OrderItem, ProcessorResult
from app.processors.registry import register

W_MM, H_MM = 200, 120
COLOURED_HEX = {"Copper": "#B87333", "Gold": "#FFD700", "Silver": "#C0C0C0", "Stone": "#8B8680", "Marble": "#E8E0D8"}


def _text_lines(dwg, item, x, fill):
    lines = [(item.line_1, 35, "9", "bold"), (item.line_2, 55, "7", "normal"), (item.line_3, 70, "6", "italic")]
    for text, y, size, weight in lines:
        if text:
            dwg.add(dwg.text(text, insert=(x, y), text_anchor="start", font_size=size, font_family="Georgia",
                             font_weight=weight if weight != "italic" else "normal",
                             font_style="italic" if weight == "italic" else "normal", fill=fill))


@register("large_stakes_graphic_coloured")
class LargeStakesGraphicColoured(BaseProcessor):
    display_name = "Large Stake — Coloured Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)
            dwg = svgwrite.Drawing(filepath, size=(f"{W_MM}mm", f"{H_MM}mm"), viewBox=f"0 0 {W_MM} {H_MM}")

            dwg.add(dwg.rect(insert=(0, 0), size=(W_MM, H_MM), fill="#f5f0e8"))
            dwg.add(dwg.rect(insert=(3, 3), size=(W_MM - 6, H_MM - 6), fill="none", stroke="#8B7355", stroke_width=1))

            graphic_name = item.graphic or "No graphic"
            if graphic_name.lower().endswith(".png"):
                graphic_name = graphic_name[:-4]
            dwg.add(dwg.rect(insert=(8, 12), size=(55, 55), fill="#e0d8c8", stroke="#8B7355", stroke_width=0.3))
            dwg.add(dwg.text(graphic_name, insert=(35, 72), text_anchor="middle", font_size="5", font_family="Georgia", fill="#666"))

            _text_lines(dwg, item, 75, "#333")

            colour_hex = COLOURED_HEX.get(item.colour, "#C0C0C0")
            dwg.add(dwg.rect(insert=(0, H_MM - 4), size=(W_MM, 4), fill=colour_hex))

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)
        except Exception as e:
            return ProcessorResult(success=False, error=str(e))


@register("large_stakes_graphic_bw")
class LargeStakesGraphicBW(BaseProcessor):
    display_name = "Large Stake — B&W Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)
            dwg = svgwrite.Drawing(filepath, size=(f"{W_MM}mm", f"{H_MM}mm"), viewBox=f"0 0 {W_MM} {H_MM}")

            dwg.add(dwg.rect(insert=(0, 0), size=(W_MM, H_MM), fill="#1a1a1a"))
            dwg.add(dwg.rect(insert=(3, 3), size=(W_MM - 6, H_MM - 6), fill="none", stroke="#fff", stroke_width=1))

            graphic_name = item.graphic or "No graphic"
            if graphic_name.lower().endswith(".png"):
                graphic_name = graphic_name[:-4]
            dwg.add(dwg.rect(insert=(8, 12), size=(55, 55), fill="#333", stroke="#666", stroke_width=0.3))
            dwg.add(dwg.text(graphic_name, insert=(35, 72), text_anchor="middle", font_size="5", font_family="Georgia", fill="#999"))

            _text_lines(dwg, item, 75, "#fff")

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)
        except Exception as e:
            return ProcessorResult(success=False, error=str(e))


@register("large_stakes_photo_coloured")
class LargeStakesPhotoColoured(BaseProcessor):
    display_name = "Large Stake — Coloured Photo"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)
            dwg = svgwrite.Drawing(filepath, size=(f"{W_MM}mm", f"{H_MM}mm"), viewBox=f"0 0 {W_MM} {H_MM}")

            dwg.add(dwg.rect(insert=(0, 0), size=(W_MM, H_MM), fill="#f5f0e8"))
            dwg.add(dwg.rect(insert=(3, 3), size=(W_MM - 6, H_MM - 6), fill="none", stroke="#8B7355", stroke_width=1))

            photo_x, photo_y, photo_w, photo_h = 8, 10, 60, 75
            dwg.add(dwg.rect(insert=(photo_x, photo_y), size=(photo_w, photo_h), fill="#ddd", stroke="#8B7355", stroke_width=0.5))
            if item.image_path and os.path.exists(item.image_path):
                dwg.add(dwg.image(href=item.image_path, insert=(photo_x, photo_y), size=(photo_w, photo_h), preserveAspectRatio="xMidYMid slice"))
            else:
                dwg.add(dwg.text("PHOTO", insert=(photo_x + photo_w / 2, photo_y + photo_h / 2), text_anchor="middle", dominant_baseline="central", font_size="6", font_family="Arial", fill="#999"))

            _text_lines(dwg, item, 80, "#333")

            colour_hex = COLOURED_HEX.get(item.colour, "#C0C0C0")
            dwg.add(dwg.rect(insert=(0, H_MM - 4), size=(W_MM, 4), fill=colour_hex))

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)
        except Exception as e:
            return ProcessorResult(success=False, error=str(e))


@register("large_stakes_photo_bw")
class LargeStakesPhotoBW(BaseProcessor):
    display_name = "Large Stake — B&W Photo"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)
            dwg = svgwrite.Drawing(filepath, size=(f"{W_MM}mm", f"{H_MM}mm"), viewBox=f"0 0 {W_MM} {H_MM}")

            dwg.add(dwg.rect(insert=(0, 0), size=(W_MM, H_MM), fill="#1a1a1a"))
            dwg.add(dwg.rect(insert=(3, 3), size=(W_MM - 6, H_MM - 6), fill="none", stroke="#fff", stroke_width=1))

            photo_x, photo_y, photo_w, photo_h = 8, 10, 60, 75
            dwg.add(dwg.rect(insert=(photo_x, photo_y), size=(photo_w, photo_h), fill="#333", stroke="#666", stroke_width=0.5))
            if item.image_path and os.path.exists(item.image_path):
                dwg.add(dwg.image(href=item.image_path, insert=(photo_x, photo_y), size=(photo_w, photo_h), preserveAspectRatio="xMidYMid slice"))
            else:
                dwg.add(dwg.text("PHOTO", insert=(photo_x + photo_w / 2, photo_y + photo_h / 2), text_anchor="middle", dominant_baseline="central", font_size="6", font_family="Arial", fill="#666"))

            _text_lines(dwg, item, 80, "#fff")

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)
        except Exception as e:
            return ProcessorResult(success=False, error=str(e))
