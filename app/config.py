from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "PaddleOCR Service"
    service_version: str = "2.0.0"
    ocr_use_gpu: bool = False

    default_invoice_compute_mode: str = "local"
    invoice_remote_base_url: str | None = None
    invoice_remote_parse_path: str = "/v1/parse"
    invoice_remote_api_key: str | None = None
    invoice_remote_timeout_sec: float = 30.0

    invoice_local_image_max_bytes: int = 12 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
