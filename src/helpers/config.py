from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str
    OPENAI_API_KEY: str
    FILE_ALLOWED_TYPES: list[str]
    FILE_MAX_SIZE_MB: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings():
    return Settings()

