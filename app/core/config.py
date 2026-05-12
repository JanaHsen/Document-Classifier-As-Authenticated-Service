from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = Field("Document Classifier Service", env="APP_NAME")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    DEBUG: bool = Field(False, env="DEBUG")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    # API
    API_HOST: str = Field("0.0.0.0", env="API_HOST")
    API_PORT: int = Field(8000, env="API_PORT")
    API_WORKERS: int = Field(4, env="API_WORKERS")

    # Database
    DATABASE_URL: str = Field(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/document_classifier",
        env="DATABASE_URL",
    )
    DATABASE_SYNC_URL: str = Field(
        "postgresql://postgres:postgres@localhost:5432/document_classifier",
        env="DATABASE_SYNC_URL",
    )
    DATABASE_POOL_SIZE: int = Field(20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(0, env="DATABASE_MAX_OVERFLOW")

    # Redis
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    REDIS_CACHE_TTL: int = Field(300, env="REDIS_CACHE_TTL")

    # MinIO
    MINIO_ENDPOINT: str = Field("localhost:9000", env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field("minioadmin", env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field("minioadmin", env="MINIO_SECRET_KEY")
    MINIO_BUCKET_RAW: str = Field("raw", env="MINIO_BUCKET_RAW")
    MINIO_BUCKET_OVERLAYS: str = Field("overlays", env="MINIO_BUCKET_OVERLAYS")
    MINIO_SECURE: bool = Field(False, env="MINIO_SECURE")

    # JWT
    JWT_SECRET_KEY: str = Field("dev-secret-key-change-in-production", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(1440, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # Classifier
    CLASSIFIER_MODEL_PATH: str = Field("/app/app/classifier/models/classifier.pt", env="CLASSIFIER_MODEL_PATH")
    CLASSIFIER_MODEL_CARD_PATH: str = Field("/app/app/classifier/models/model_card.json", env="CLASSIFIER_MODEL_CARD_PATH")
    CLASSIFIER_CONFIDENCE_THRESHOLD: float = Field(0.5, env="CLASSIFIER_CONFIDENCE_THRESHOLD")
    CLASSIFIER_BATCH_SIZE: int = Field(8, env="CLASSIFIER_BATCH_SIZE")

    # Workers
    WORKER_INGEST_POLL_INTERVAL: int = Field(10, env="WORKER_INGEST_POLL_INTERVAL")
    WORKER_INFERENCE_TIMEOUT: int = Field(300, env="WORKER_INFERENCE_TIMEOUT")
    WORKER_MAX_RETRIES: int = Field(3, env="WORKER_MAX_RETRIES")

    # SFTP
    SFTP_HOST: str = Field("localhost", env="SFTP_HOST")
    SFTP_PORT: int = Field(22, env="SFTP_PORT")
    SFTP_USER: str = Field("upload", env="SFTP_USER")
    SFTP_PASSWORD: str = Field("upload", env="SFTP_PASSWORD")
    SFTP_UPLOAD_DIR: str = Field("/uploads", env="SFTP_UPLOAD_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
