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
