"""Settings router — key/value store for runtime-adjustable global settings.

Currently powers print calibration (content offsets). Can be extended for
any other global settings that need adjusting without a redeploy.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AppSetting

router = APIRouter(prefix="/api/settings", tags=["Settings"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_float(db: Session, key: str, default: float = 0.0) -> float:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row is None:
        return default
    try:
        return float(row.value)
    except (TypeError, ValueError):
        return default


def _set_value(db: Session, key: str, value: str) -> None:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row is None:
        db.add(AppSetting(key=key, value=value))
    else:
        row.value = value
    db.commit()


def get_calibration(db: Session) -> dict:
    """Fetch the global print calibration. Used by generate.py."""
    return {
        "x_mm": _get_float(db, "calibration.x_mm", 0.0),
        "y_mm": _get_float(db, "calibration.y_mm", 0.0),
    }


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

class Calibration(BaseModel):
    x_mm: float
    y_mm: float


@router.get("/calibration", response_model=Calibration)
def read_calibration(db: Session = Depends(get_db)):
    """Get the current global print calibration offset (mm).

    Applied to ALL generated memorials. Compensates for physical
    printer/cutter alignment offsets.
    """
    return get_calibration(db)


@router.put("/calibration", response_model=Calibration)
def update_calibration(calib: Calibration, db: Session = Depends(get_db)):
    """Set the global print calibration offset (mm).

    Takes effect on the next generate run — no restart needed.
    """
    _set_value(db, "calibration.x_mm", str(calib.x_mm))
    _set_value(db, "calibration.y_mm", str(calib.y_mm))
    return calib
