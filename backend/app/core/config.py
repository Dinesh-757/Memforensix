"""
Application configuration management using Pydantic BaseSettings.
Loads values from environment variables / .env file.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "MEMFORENSIX"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default="CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_32")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    POSTGRES_USER: str = "memforensix"
    POSTGRES_PASSWORD: str = "memforensix_pass"
    POSTGRES_DB: str = "memforensix"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis / Celery
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # File storage
    UPLOAD_DIR: str = "/data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 4096
    ALLOWED_EXTENSIONS: List[str] = [".raw", ".dmp", ".mem", ".vmem", ".elf", ".core"]

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]

    # YARA
    YARA_RULES_DIR: str = "/app/yara_rules"

    def model_post_init(self, __context) -> None:
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
