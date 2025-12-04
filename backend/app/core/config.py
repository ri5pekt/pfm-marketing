from pydantic_settings import BaseSettings
from typing import List, Union
import os


class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@db:5432/pfm_marketing"
    REDIS_URL: str = "redis://redis:6379/0"
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:3000"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

