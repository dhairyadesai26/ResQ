"""
ResQ Web - Backend Configuration Settings
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ResQ Web"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Server binding
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # CORS origins
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Database
    DATABASE_URL: str = "sqlite:///./resq.db"

    # Monitoring intervals
    METRICS_COLLECTION_INTERVAL_SECONDS: float = 2.0
    SUPERVISOR_SECRET: str = "resq-local-secret-2026"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

