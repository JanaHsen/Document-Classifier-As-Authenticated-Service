# Owner: HADI
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    # Toggles SQLAlchemy SQL echo (every query printed to stdout). Off in prod, on for local debugging.
    DEBUG: bool = False

    # Database — Tarek's session.py reads these exact field names
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/docclassifier"
    DATABASE_SYNC_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/docclassifier"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "documents"
    MINIO_SECURE: bool = False

    # Vault
    VAULT_ADDR: str = "http://localhost:8200"
    VAULT_TOKEN: str = ""


settings = Settings()
