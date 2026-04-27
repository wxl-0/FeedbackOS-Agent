from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    use_mock_llm: bool = True
    database_url: str = "sqlite:///./storage/feedbackos.db"
    redis_url: str = "redis://localhost:6379/0"
    milvus_lite_path: str = "./storage/milvus_lite.db"
    frontend_origin: str = "http://localhost:3000"
    upload_dir: Path = Path("uploads")
    export_dir: Path = Path("storage/exports")
    prd_dir: Path = Path("storage/prds")

    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    @property
    def real_llm_enabled(self) -> bool:
        return bool(self.openai_api_key) and not self.use_mock_llm


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    settings.prd_dir.mkdir(parents=True, exist_ok=True)
    return settings
