from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./memorials.db"
    SECRET_KEY: str = "change-me"
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./output"
    GRAPHICS_DIR: str = "./assets/graphics"

    # SMTP settings for bug reports
    SMTP_HOST: str = "smtp.ionos.co.uk"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = ""
    SMTP_TO: str = ""  # comma-separated recipient list

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Ensure directories exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
if settings.GRAPHICS_DIR and not Path(settings.GRAPHICS_DIR).exists():
    import logging
    logging.warning(f"GRAPHICS_DIR does not exist: {settings.GRAPHICS_DIR}")
