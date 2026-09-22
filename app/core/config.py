import os
from pydantic_settings import BaseSettings
 
 
class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "development")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "app/models/model.pkl")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
 
    # --- Auth / JWT ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
 
    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./reactor.db")
 
    class Config:
        env_file = ".env"
 
 
settings = Settings()
 
