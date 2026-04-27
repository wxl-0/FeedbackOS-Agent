import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    use_mock_llm: bool = False
    database_url: str = "sqlite:///./storage/feedbackos.db"
    redis_url: str = "redis://localhost:6379/0"
    milvus_lite_path: str = "./storage/milvus_lite.db"
    frontend_origin: str = "http://localhost:3000"
    upload_dir: Path = Path("uploads")
    export_dir: Path = Path("storage/exports")
    prd_dir: Path = Path("storage/prds")

    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    @property
    def llm_api_key(self) -> str | None:
        if os.getenv("DASHSCOPE_API_KEY") and not os.getenv("OPENAI_BASE_URL"):
            return os.getenv("DASHSCOPE_API_KEY")
        return (
            self.openai_api_key
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("DASHSCOPE_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("SILICONFLOW_API_KEY")
        )

    @property
    def resolved_base_url(self) -> str:
        if os.getenv("OPENAI_BASE_URL"):
            return self.openai_base_url
        if os.getenv("DASHSCOPE_API_KEY"):
            return "https://dashscope.aliyuncs.com/compatible-mode/v1"
        if os.getenv("DEEPSEEK_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            return "https://api.deepseek.com/v1"
        return self.openai_base_url

    @property
    def resolved_model(self) -> str:
        if os.getenv("OPENAI_MODEL"):
            return self.openai_model
        if os.getenv("DASHSCOPE_API_KEY"):
            return "qwen-plus"
        if os.getenv("DEEPSEEK_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            return "deepseek-chat"
        return self.openai_model

    @property
    def resolved_embedding_model(self) -> str:
        if os.getenv("EMBEDDING_MODEL"):
            return self.embedding_model
        if os.getenv("DASHSCOPE_API_KEY"):
            return "text-embedding-v4"
        return self.embedding_model

    @property
    def real_llm_enabled(self) -> bool:
        return bool(self.llm_api_key) and not self.use_mock_llm


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    settings.prd_dir.mkdir(parents=True, exist_ok=True)
    return settings
