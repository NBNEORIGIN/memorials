"""Processor registry — maps processor_key strings to processor classes.

Usage:
    from app.processors.registry import get_processor
    processor = get_processor("regular_stakes_graphic_coloured", graphics_dir, output_dir)
    result = processor.generate_svg(item, output_dir)
"""

from typing import Optional
from app.processors.base import BaseProcessor


# Registry populated by processor modules on import
_REGISTRY: dict[str, type[BaseProcessor]] = {}


def register(key: str):
    """Decorator to register a processor class under a given key."""
    def wrapper(cls: type[BaseProcessor]):
        cls.processor_key = key
        _REGISTRY[key] = cls
        return cls
    return wrapper


def get_processor(key: str, graphics_dir: str, output_dir: str) -> Optional[BaseProcessor]:
    """Look up and instantiate a processor by key. Returns None if not found."""
    cls = _REGISTRY.get(key)
    if cls is None:
        return None
    return cls(graphics_dir, output_dir)


def list_registered() -> list[str]:
    """Return all registered processor keys."""
    return sorted(_REGISTRY.keys())


# Import all processor modules so they self-register via @register decorator.
# Add new processor imports here as they are ported.
def _import_all():
    try:
        from app.processors import regular_stakes_graphic  # noqa: F401
    except ImportError:
        pass


_import_all()
