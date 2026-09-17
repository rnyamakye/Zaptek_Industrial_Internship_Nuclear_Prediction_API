import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "development")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "app/models/model.pkl")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")

    class Config:
        env_file = ".env"


settings = Settings()
