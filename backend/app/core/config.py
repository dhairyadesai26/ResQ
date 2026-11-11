"""
ResQ Web - Backend Configuration Settings
"""

import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ResQ Web"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Server binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # CORS origins
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Database
    DATABASE_URL: str = "sqlite:///./resq.db"

    # Monitoring intervals
    METRICS_COLLECTION_INTERVAL_SECONDS: float = 2.0
    SUPERVISOR_SECRET: str = "resq-local-secret-2026"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

