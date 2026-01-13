from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    concurrent_limit: int = 10
    encoding: str = "utf-8"
    chunk_size: int = 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
