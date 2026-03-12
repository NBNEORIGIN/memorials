"""Regular Stakes — Graphic processors (coloured and B&W).

These are stub implementations. The SVG generation logic will be ported
from AmazonPhotoProcessor 2 / 002 D2C WRITER / regular_stakes.py.
"""

import os
import svgwrite

from app.processors.base import BaseProcessor, OrderItem, ProcessorResult
from app.processors.registry import register


@register("regular_stakes_graphic_coloured")
class RegularStakesGraphicColoured(BaseProcessor):
    display_name = "Regular Stake — Coloured Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)

            # Dimensions for regular stake: 140mm x 90mm
            w_mm, h_mm = 140, 90
            dwg = svgwrite.Drawing(
                filepath,
                size=(f"{w_mm}mm", f"{h_mm}mm"),
                viewBox=f"0 0 {w_mm} {h_mm}",
            )

            # Background
            dwg.add(dwg.rect(insert=(0, 0), size=(w_mm, h_mm), fill="#f5f0e8"))

            # Border
            dwg.add(dwg.rect(
                insert=(2, 2), size=(w_mm - 4, h_mm - 4),
                fill="none", stroke="#8B7355", stroke_width=0.8,
            ))

            # Graphic placeholder (left side)
            graphic_name = item.graphic or "No graphic"
            if graphic_name.lower().endswith(".png"):
                graphic_name = graphic_name[:-4]
            dwg.add(dwg.rect(
                insert=(5, 10), size=(40, 40),
                fill="#e0d8c8", stroke="#8B7355", stroke_width=0.3,
            ))
            dwg.add(dwg.text(
                graphic_name,
                insert=(25, 55), text_anchor="middle",
                font_size="4", font_family="Georgia", fill="#666",
            ))

            # Text lines (right side)
            x_text = 55
            lines = [
                (item.line_1, 25, "7", "bold"),
                (item.line_2, 40, "5.5", "normal"),
                (item.line_3, 52, "5", "italic"),
            ]
            for text, y, size, weight in lines:
                if text:
                    dwg.add(dwg.text(
                        text,
                        insert=(x_text, y), text_anchor="start",
                        font_size=size, font_family="Georgia",
                        font_weight=weight if weight != "italic" else "normal",
                        font_style="italic" if weight == "italic" else "normal",
                        fill="#333",
                    ))

            # Colour indicator
            colour_hex = {
                "Copper": "#B87333", "Gold": "#FFD700", "Silver": "#C0C0C0",
                "Stone": "#8B8680", "Marble": "#E8E0D8",
            }.get(item.colour, "#C0C0C0")
            dwg.add(dwg.rect(
                insert=(0, h_mm - 3), size=(w_mm, 3), fill=colour_hex,
            ))

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)

        except Exception as e:
            return ProcessorResult(success=False, error=str(e))


@register("regular_stakes_graphic_bw")
class RegularStakesGraphicBW(BaseProcessor):
    display_name = "Regular Stake — B&W Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        try:
            filename = self.build_filename(item)
            filepath = os.path.join(output_dir, filename)

            w_mm, h_mm = 140, 90
            dwg = svgwrite.Drawing(
                filepath,
                size=(f"{w_mm}mm", f"{h_mm}mm"),
                viewBox=f"0 0 {w_mm} {h_mm}",
            )

            # Black background
            dwg.add(dwg.rect(insert=(0, 0), size=(w_mm, h_mm), fill="#1a1a1a"))

            # Border
            dwg.add(dwg.rect(
                insert=(2, 2), size=(w_mm - 4, h_mm - 4),
                fill="none", stroke="#fff", stroke_width=0.8,
            ))

            # Graphic placeholder
            graphic_name = item.graphic or "No graphic"
            if graphic_name.lower().endswith(".png"):
                graphic_name = graphic_name[:-4]
            dwg.add(dwg.rect(
                insert=(5, 10), size=(40, 40),
                fill="#333", stroke="#666", stroke_width=0.3,
            ))
            dwg.add(dwg.text(
                graphic_name,
                insert=(25, 55), text_anchor="middle",
                font_size="4", font_family="Georgia", fill="#999",
            ))

            # Text lines
            x_text = 55
            lines = [
                (item.line_1, 25, "7", "bold"),
                (item.line_2, 40, "5.5", "normal"),
                (item.line_3, 52, "5", "italic"),
            ]
            for text, y, size, weight in lines:
                if text:
                    dwg.add(dwg.text(
                        text,
                        insert=(x_text, y), text_anchor="start",
                        font_size=size, font_family="Georgia",
                        font_weight=weight if weight != "italic" else "normal",
                        font_style="italic" if weight == "italic" else "normal",
                        fill="#fff",
                    ))

            dwg.save()
            return ProcessorResult(success=True, svg_path=filepath)

        except Exception as e:
            return ProcessorResult(success=False, error=str(e))
