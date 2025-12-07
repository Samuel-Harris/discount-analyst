from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Pydantic(BaseModel):
    ai_gateway_api_key: str
    logfire_api_key: str


class Perplexity(BaseModel):
    api_key: str
    rate_limit_per_minute: int


class DataFetcher(BaseModel):
    search_tool_call_limit: int


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    pydantic: Pydantic
    perplexity: Perplexity
    data_fetcher: DataFetcher


settings = Settings()
