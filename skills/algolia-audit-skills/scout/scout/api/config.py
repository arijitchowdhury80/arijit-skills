"""Scout API configuration — loads settings from environment or .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings resolved from environment variables or .env file."""

    scout_api_key: str = "dev-key"
    llm_api_key: str = ""
    host: str = "0.0.0.0"
    port: int = 8421

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
