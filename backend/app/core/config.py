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

    # CORS origins (supports '*' wildcard, comma-separated string, or JSON list)
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if item]
                except Exception:
                    pass
            if "," in v:
                return [item.strip() for item in v.split(",") if item.strip()]
            return [v] if v else ["*"]
        elif isinstance(v, list):
            return [str(item).strip() for item in v if item]
        return ["*"]

    # Database
    DATABASE_URL: str = "sqlite:///./resq.db"

    # Monitoring intervals
    METRICS_COLLECTION_INTERVAL_SECONDS: float = 2.0
    SUPERVISOR_SECRET: str = "resq-local-secret-2026"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

