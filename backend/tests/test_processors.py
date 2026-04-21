"""Processor registry tests."""

from app.processors.registry import list_registered


EXPECTED_KEYS = [
    "brass_plaque_large",
    "brass_plaque_medium",
    "brass_plaque_small",
    "heart_stakes_graphic",
    "heart_stakes_graphic_coloured",
    "large_metal_graphic",
    "large_stakes_graphic_bw",
    "large_stakes_graphic_coloured",
    "large_stakes_photo_bw",
    "large_stakes_photo_coloured",
    "laser_engrave_large",
    "laser_engrave_medium",
    "laser_engrave_small",
    "medium_metal_graphic",
    "regular_stakes_graphic_bw",
    "regular_stakes_graphic_coloured",
    "regular_stakes_photo_bw",
    "regular_stakes_photo_coloured",
    "small_metal_graphic",
    "small_stakes_graphic_bw",
    "small_stakes_graphic_coloured",
    "xl_metal_graphic",
]


def test_all_processors_registered():
    registered = list_registered()
    assert registered == EXPECTED_KEYS


def test_processor_count():
    assert len(list_registered()) == 22


def test_content_calibration_offset_default():
    """Default calibration is 0 — mathematically centred. Overridable
    via BaseProcessor subclass or CellLayout if physical calibration
    is ever needed."""
    from app.processors.base import BaseProcessor
    assert BaseProcessor.content_x_offset_mm == 0.0
    assert BaseProcessor.content_y_offset_mm == 0.0


def test_content_offset_overridable_via_layout():
    """Layout overrides must be able to tweak the calibration per processor/SKU."""
    from app.processors.registry import get_processor
    proc = get_processor(
        "regular_stakes_graphic_coloured", "/tmp", "/tmp",
        layout_overrides={"content_x_offset_mm": -2.0},
    )
    assert proc is not None
    assert proc.lv("content_x_offset_mm") == -2.0
