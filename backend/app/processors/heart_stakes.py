"""Heart Stakes — graphic coloured and generic graphic."""

import os
import svgwrite

from app.processors.base import BaseProcessor, OrderItem, ProcessorResult
from app.processors.registry import register

W_MM, H_MM = 140, 140


def _heart_path():
    """SVG path for a heart shape scaled to ~140x140mm viewBox."""
    return "M70 125 C20 90, 0 50, 0 35 C0 15, 15 0, 35 0 C50 0, 62 10, 70 25 C78 10, 90 0, 105 0 C125 0, 140 15, 140 35 C140 50, 120 90, 70 125 Z"


@register("heart_stakes_graphic_coloured")
class HeartStakesGraphicColoured(BaseProcessor):
    display_name = "Heart Stake — Coloured Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)
            dwg = svgwrite.Drawing(filepath, size=(f"{W_MM}mm", f"{H_MM}mm"), viewBox=f"0 0 {W_MM} {H_MM}")

            colour_hex = {"Copper": "#B87333", "Gold": "#FFD700", "Silver": "#C0C0C0", "Stone": "#8B8680", "Marble": "#E8E0D8"}.get(item.colour, "#C0C0C0")

            dwg.add(dwg.rect(insert=(0, 0), size=(W_MM, H_MM), fill="#f5f0e8"))
            dwg.add(dwg.path(d=_heart_path(), fill="none", stroke=colour_hex, stroke_width=2))

            graphic_name = item.graphic or "No graphic"
            if graphic_name.lower().endswith(".png"):
                graphic_name = graphic_name[:-4]
            dwg.add(dwg.rect(insert=(45, 30), size=(50, 35), fill="#e0d8c8", stroke="#8B7355", stroke_width=0.3))
            dwg.add(dwg.text(graphic_name, insert=(70, 70), text_anchor="middle", font_size="4", font_family="Georgia", fill="#666"))

            lines = [(item.line_1, 82, "6", "bold"), (item.line_2, 95, "5", "normal"), (item.line_3, 106, "4.5", "italic")]
            for text, y, size, weight in lines:
                if text:
                    dwg.add(dwg.text(text, insert=(70, y), text_anchor="middle", font_size=size, font_family="Georgia",
                                     font_weight=weight if weight != "italic" else "normal",
                                     font_style="italic" if weight == "italic" else "normal", fill="#333"))

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)
        except Exception as e:
            return ProcessorResult(success=False, error=str(e))


@register("heart_stakes_graphic")
class HeartStakesGraphic(BaseProcessor):
    display_name = "Heart Stake — Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)
            dwg = svgwrite.Drawing(filepath, size=(f"{W_MM}mm", f"{H_MM}mm"), viewBox=f"0 0 {W_MM} {H_MM}")

            dwg.add(dwg.rect(insert=(0, 0), size=(W_MM, H_MM), fill="#1a1a1a"))
            dwg.add(dwg.path(d=_heart_path(), fill="none", stroke="#fff", stroke_width=2))

            graphic_name = item.graphic or "No graphic"
            if graphic_name.lower().endswith(".png"):
                graphic_name = graphic_name[:-4]
            dwg.add(dwg.rect(insert=(45, 30), size=(50, 35), fill="#333", stroke="#666", stroke_width=0.3))
            dwg.add(dwg.text(graphic_name, insert=(70, 70), text_anchor="middle", font_size="4", font_family="Georgia", fill="#999"))

            lines = [(item.line_1, 82, "6", "bold"), (item.line_2, 95, "5", "normal"), (item.line_3, 106, "4.5", "italic")]
            for text, y, size, weight in lines:
                if text:
                    dwg.add(dwg.text(text, insert=(70, y), text_anchor="middle", font_size=size, font_family="Georgia",
                                     font_weight=weight if weight != "italic" else "normal",
                                     font_style="italic" if weight == "italic" else "normal", fill="#fff"))

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)
        except Exception as e:
            return ProcessorResult(success=False, error=str(e))
