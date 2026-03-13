from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MemorialType(Base):
    """Product types: Regular Stake, Large Stake, Small Stake, Heart Stake, etc."""
    __tablename__ = "memorial_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    dimensions_mm: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sku_mappings: Mapped[list["SkuMapping"]] = relationship(back_populates="memorial_type")


class Colour(Base):
    """Available colours: Copper, Gold, Silver, Black, Slate, etc."""
    __tablename__ = "colours"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hex_code: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    is_bw: Mapped[bool] = mapped_column(Boolean, default=False)

    sku_mappings: Mapped[list["SkuMapping"]] = relationship(back_populates="colour")


class DecorationType(Base):
    """Graphic, Photo, etc."""
    __tablename__ = "decoration_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    sku_mappings: Mapped[list["SkuMapping"]] = relationship(back_populates="decoration_type")


class Theme(Base):
    """Optional themes: Pet, Islamic, Baby, etc."""
    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    sku_mappings: Mapped[list["SkuMapping"]] = relationship(back_populates="theme")


class Processor(Base):
    """Registry of available SVG processors."""
    __tablename__ = "processors"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sku_mappings: Mapped[list["SkuMapping"]] = relationship(back_populates="processor")


class Graphic(Base):
    """Graphic assets available for use in SVG generation."""
    __tablename__ = "graphics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    theme_id: Mapped[Optional[int]] = mapped_column(ForeignKey("themes.id"), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    theme: Mapped[Optional["Theme"]] = relationship()


class SkuMapping(Base):
    """Maps Amazon/Etsy SKUs to memorial type, colour, decoration, theme, and processor.
    This replaces SKULIST.csv with a proper database table."""
    __tablename__ = "sku_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    colour_id: Mapped[int] = mapped_column(ForeignKey("colours.id"), nullable=False)
    memorial_type_id: Mapped[int] = mapped_column(ForeignKey("memorial_types.id"), nullable=False)
    decoration_type_id: Mapped[Optional[int]] = mapped_column(ForeignKey("decoration_types.id"), nullable=True)
    theme_id: Mapped[Optional[int]] = mapped_column(ForeignKey("themes.id"), nullable=True)
    processor_id: Mapped[int] = mapped_column(ForeignKey("processors.id"), nullable=False)

    colour: Mapped["Colour"] = relationship(back_populates="sku_mappings")
    memorial_type: Mapped["MemorialType"] = relationship(back_populates="sku_mappings")
    decoration_type: Mapped[Optional["DecorationType"]] = relationship(back_populates="sku_mappings")
    theme: Mapped[Optional["Theme"]] = relationship(back_populates="sku_mappings")
    processor: Mapped["Processor"] = relationship(back_populates="sku_mappings")


class Job(Base):
    """A batch processing job (one file upload = one job)."""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), default="amazon")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    filename: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["JobItem"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class JobItem(Base):
    """Individual order item within a job."""
    __tablename__ = "job_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    order_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    order_item_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    sku: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Resolved from SKU mapping (or overridden manually)
    colour: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    memorial_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    decoration_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    theme: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    processor_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Personalisation data from order
    graphic: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    line_1: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    line_2: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    line_3: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Output
    svg_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="items")


class CellLayout(Base):
    """Per-processor cell layout overrides.

    Stores text positions, font sizes, graphic/photo placement as JSON.
    Processors read these at generation time, falling back to class defaults
    if no layout is stored. Staff can adjust via the visual layout editor.
    """
    __tablename__ = "cell_layouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    processor_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    label: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Text positions (Y-offset in mm from cell top)
    line1_y_mm: Mapped[Optional[float]] = mapped_column(nullable=True)
    line2_y_mm: Mapped[Optional[float]] = mapped_column(nullable=True)
    line3_y_mm: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Font sizes in pt
    line1_size_pt: Mapped[Optional[float]] = mapped_column(nullable=True)
    line2_size_pt: Mapped[Optional[float]] = mapped_column(nullable=True)
    line3_size_pt: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Text X position as fraction of cell width (0.5 = centred)
    text_x_frac: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Graphic position/size as fractions of cell dimensions
    graphic_x_frac: Mapped[Optional[float]] = mapped_column(nullable=True)
    graphic_y_frac: Mapped[Optional[float]] = mapped_column(nullable=True)
    graphic_w_frac: Mapped[Optional[float]] = mapped_column(nullable=True)
    graphic_h_frac: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Photo position/size as fractions of cell dimensions (photo processors)
    photo_x_frac: Mapped[Optional[float]] = mapped_column(nullable=True)
    photo_y_frac: Mapped[Optional[float]] = mapped_column(nullable=True)
    photo_w_frac: Mapped[Optional[float]] = mapped_column(nullable=True)
    photo_h_frac: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Max chars per line for word-wrap
    max_chars_line1: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_chars_line2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_chars_line3: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Line 3 max rows
    line3_max_rows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Font family override
    font_family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Text colour
    text_fill: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)
