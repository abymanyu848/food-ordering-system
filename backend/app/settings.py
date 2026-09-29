from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_DB_PATH = BACKEND_DIR / "food_ordering.db"


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Food Ordering Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "ug-mini-project-development-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    # Database: a local SQLite file keeps the project easy to run and demonstrate.
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self.DATABASE_URL

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(case_sensitive=True, env_file=(str(PROJECT_ROOT / ".env"), str(BACKEND_DIR / ".env")), extra="ignore")


settings = Settings()