"""Small Stakes — graphic coloured and graphic B&W."""

import os
import svgwrite

from app.processors.base import BaseProcessor, OrderItem, ProcessorResult
from app.processors.registry import register

W_MM, H_MM = 100, 60


@register("small_stakes_graphic_coloured")
class SmallStakesGraphicColoured(BaseProcessor):
    display_name = "Small Stake — Coloured Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)
            dwg = svgwrite.Drawing(filepath, size=(f"{W_MM}mm", f"{H_MM}mm"), viewBox=f"0 0 {W_MM} {H_MM}")

            dwg.add(dwg.rect(insert=(0, 0), size=(W_MM, H_MM), fill="#f5f0e8"))
            dwg.add(dwg.rect(insert=(1.5, 1.5), size=(W_MM - 3, H_MM - 3), fill="none", stroke="#8B7355", stroke_width=0.6))

            graphic_name = item.graphic or "No graphic"
            if graphic_name.lower().endswith(".png"):
                graphic_name = graphic_name[:-4]
            dwg.add(dwg.rect(insert=(4, 6), size=(28, 28), fill="#e0d8c8", stroke="#8B7355", stroke_width=0.3))
            dwg.add(dwg.text(graphic_name, insert=(18, 38), text_anchor="middle", font_size="3", font_family="Georgia", fill="#666"))

            x_text = 38
            lines = [(item.line_1, 16, "5", "bold"), (item.line_2, 28, "4", "normal"), (item.line_3, 38, "3.5", "italic")]
            for text, y, size, weight in lines:
                if text:
                    dwg.add(dwg.text(text, insert=(x_text, y), text_anchor="start", font_size=size, font_family="Georgia",
                                     font_weight=weight if weight != "italic" else "normal",
                                     font_style="italic" if weight == "italic" else "normal", fill="#333"))

            colour_hex = {"Copper": "#B87333", "Gold": "#FFD700", "Silver": "#C0C0C0", "Stone": "#8B8680", "Marble": "#E8E0D8"}.get(item.colour, "#C0C0C0")
            dwg.add(dwg.rect(insert=(0, H_MM - 2), size=(W_MM, 2), fill=colour_hex))

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)
        except Exception as e:
            return ProcessorResult(success=False, error=str(e))


@register("small_stakes_graphic_bw")
class SmallStakesGraphicBW(BaseProcessor):
    display_name = "Small Stake — B&W Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)
            dwg = svgwrite.Drawing(filepath, size=(f"{W_MM}mm", f"{H_MM}mm"), viewBox=f"0 0 {W_MM} {H_MM}")

            dwg.add(dwg.rect(insert=(0, 0), size=(W_MM, H_MM), fill="#1a1a1a"))
            dwg.add(dwg.rect(insert=(1.5, 1.5), size=(W_MM - 3, H_MM - 3), fill="none", stroke="#fff", stroke_width=0.6))

            graphic_name = item.graphic or "No graphic"
            if graphic_name.lower().endswith(".png"):
                graphic_name = graphic_name[:-4]
            dwg.add(dwg.rect(insert=(4, 6), size=(28, 28), fill="#333", stroke="#666", stroke_width=0.3))
            dwg.add(dwg.text(graphic_name, insert=(18, 38), text_anchor="middle", font_size="3", font_family="Georgia", fill="#999"))

            x_text = 38
            lines = [(item.line_1, 16, "5", "bold"), (item.line_2, 28, "4", "normal"), (item.line_3, 38, "3.5", "italic")]
            for text, y, size, weight in lines:
                if text:
                    dwg.add(dwg.text(text, insert=(x_text, y), text_anchor="start", font_size=size, font_family="Georgia",
                                     font_weight=weight if weight != "italic" else "normal",
                                     font_style="italic" if weight == "italic" else "normal", fill="#fff"))

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)
        except Exception as e:
            return ProcessorResult(success=False, error=str(e))
