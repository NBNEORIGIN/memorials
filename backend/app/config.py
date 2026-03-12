from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./memorials.db"
    SECRET_KEY: str = "change-me"
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./output"
    GRAPHICS_DIR: str = r"D:\Google Drive\My Drive\003 APPS\AmazonSeller -CURRENT VERSION\assets\graphics"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Ensure directories exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
if settings.GRAPHICS_DIR:
    Path(settings.GRAPHICS_DIR).mkdir(parents=True, exist_ok=True)
