"""Application configuration loaded from environment variables / .env file."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/config.py -> project root is one level up
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    app_name: str = "MediTrack API"
    version: str = "2.0.0"
    debug: bool = True

    # Auth
    jwt_secret: str = "meditrack-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24h for demo convenience

    # Database
    sqlite_path: str = os.path.join(PROJECT_ROOT, "data", "meditrack.db")

    # ML artifacts
    model_artifact_dir: str = os.path.join(PROJECT_ROOT, "ml", "artifacts")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()