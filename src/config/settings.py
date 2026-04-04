from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    BOT_TOKEN: SecretStr

    ENV: str = "development"

    WEBHOOK_BASE_URL: str = ""
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_SECRET: SecretStr = SecretStr("")
    WEBHOOK_HOST: str = "0.0.0.0"
    WEBHOOK_PORT: int = 8080

    @property
    def is_production(self) -> bool:
        return self.ENV.strip().lower() == "production"

    @property
    def webhook_url(self) -> str:
        return f"{self.WEBHOOK_BASE_URL.rstrip('/')}{self.WEBHOOK_PATH}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(**{})
