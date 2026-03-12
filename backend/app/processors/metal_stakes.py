"""Metal processors — Large, XL, Medium, Small metal graphic stakes."""

import os
import svgwrite

from app.processors.base import BaseProcessor, OrderItem, ProcessorResult
from app.processors.registry import register

METAL_DIMS = {
    "large": (200, 120),
    "xl": (250, 150),
    "medium": (160, 100),
    "small": (120, 80),
}


def _metal_svg(item: OrderItem, output_dir: str, size_key: str, filepath: str) -> ProcessorResult:
    try:
        w_mm, h_mm = METAL_DIMS[size_key]
        dwg = svgwrite.Drawing(filepath, size=(f"{w_mm}mm", f"{h_mm}mm"), viewBox=f"0 0 {w_mm} {h_mm}")

        # Brushed metal background
        dwg.add(dwg.rect(insert=(0, 0), size=(w_mm, h_mm), fill="#d4d0c8"))
        # Metallic gradient effect
        grad = dwg.defs.add(dwg.linearGradient(id="metal_sheen", x1="0%", y1="0%", x2="100%", y2="100%"))
        grad.add_stop_color(0, "#fff", opacity=0.3)
        grad.add_stop_color(0.5, "#fff", opacity=0)
        grad.add_stop_color(1, "#fff", opacity=0.15)
        dwg.add(dwg.rect(insert=(0, 0), size=(w_mm, h_mm), fill="url(#metal_sheen)"))

        # Border
        dwg.add(dwg.rect(insert=(2, 2), size=(w_mm - 4, h_mm - 4), fill="none", stroke="#8B7355", stroke_width=0.8))

        # Text — centered layout for metal plaques
        cx = w_mm / 2
        lines = [
            (item.line_1, h_mm * 0.3, str(w_mm * 0.05), "bold"),
            (item.line_2, h_mm * 0.5, str(w_mm * 0.04), "normal"),
            (item.line_3, h_mm * 0.65, str(w_mm * 0.035), "italic"),
        ]
        for text, y, size, weight in lines:
            if text:
                dwg.add(dwg.text(
                    text, insert=(cx, y), text_anchor="middle",
                    font_size=size, font_family="Georgia",
                    font_weight=weight if weight != "italic" else "normal",
                    font_style="italic" if weight == "italic" else "normal",
                    fill="#333",
                ))

        # Material label
        colour_name = item.colour or "Metal"
        dwg.add(dwg.text(
            f"{colour_name} · {item.memorial_type}",
            insert=(cx, h_mm - 6), text_anchor="middle",
            font_size="3.5", font_family="Arial", fill="#999",
        ))

        dwg.save()
        return ProcessorResult(success=True, svg_path=filepath)
    except Exception as e:
        return ProcessorResult(success=False, error=str(e))


@register("large_metal_graphic")
class LargeMetalGraphic(BaseProcessor):
    display_name = "Large Metal — Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        filepath = os.path.join(output_dir, self.build_filename(item))
        return _metal_svg(item, output_dir, "large", filepath)


@register("xl_metal_graphic")
class XLMetalGraphic(BaseProcessor):
    display_name = "XL Metal — Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        filepath = os.path.join(output_dir, self.build_filename(item))
        return _metal_svg(item, output_dir, "xl", filepath)


@register("medium_metal_graphic")
class MediumMetalGraphic(BaseProcessor):
    display_name = "Medium Metal — Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        filepath = os.path.join(output_dir, self.build_filename(item))
        return _metal_svg(item, output_dir, "medium", filepath)


@register("small_metal_graphic")
class SmallMetalGraphic(BaseProcessor):
    display_name = "Small Metal — Graphic"

    def generate_svg(self, item: OrderItem, output_dir: str) -> ProcessorResult:
        filepath = os.path.join(output_dir, self.build_filename(item))
        return _metal_svg(item, output_dir, "small", filepath)
