from typing import List, Optional, Union
from pydantic import AliasChoices, Field, PostgresDsn, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Coffee Chain Inventory & Orders API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # PostgreSQL settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "coffee_db"

    # Optional direct DATABASE_URL override
    DATABASE_URL: Optional[str] = None

    # Telegram Bot settings
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(
        None, validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "BOT_TOKEN")
    )
    TELEGRAM_WAREHOUSE_CHAT_ID: Optional[int] = Field(
        None, validation_alias=AliasChoices("TELEGRAM_WAREHOUSE_CHAT_ID", "WAREHOUSE_CHAT_ID")
    )
    WEBAPP_URL: str = Field(
        "http://localhost:5173", validation_alias=AliasChoices("WEBAPP_URL", "MINI_APP_URL")
    )
    ADMIN_TELEGRAM_IDS: List[int] = []

    # Vision LLM / OCR settings
    GEMINI_API_KEY: Optional[str] = Field(
        None, validation_alias=AliasChoices("GEMINI_API_KEY", "AI_API_KEY")
    )
    OPENAI_API_KEY: Optional[str] = None
    OCR_PROVIDER: str = "gemini"  # "gemini" or "openai"
    OCR_MODEL: str = "gemini-2.5-flash"  # e.g. "gemini-2.5-flash", "gemini-1.5-flash", "gpt-4o-mini"

    @field_validator("ADMIN_TELEGRAM_IDS", mode="before")
    @classmethod
    def parse_admin_telegram_ids(cls, v: Union[str, List[Union[int, str]], int, None]) -> List[int]:
        if v is None:
            return []
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            # Handle JSON array string e.g. "[123, 456]" or comma-separated "123,456"
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    parsed = json.loads(v)
                    return [int(x) for x in parsed if str(x).strip()]
                except Exception:
                    pass
            parts = [x.strip() for x in v.split(",") if x.strip()]
            result: List[int] = []
            for item in parts:
                try:
                    result.append(int(item))
                except ValueError:
                    continue
            return result
        elif isinstance(v, list):
            return [int(x) for x in v if str(x).strip()]
        elif isinstance(v, int):
            return [v]
        return []

    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        if self.DATABASE_URL:
            # Ensure asyncpg driver is specified if postgresql:// was supplied
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
