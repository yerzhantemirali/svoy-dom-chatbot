from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    REDIS_URL: str = "redis://redis:6379/0"
    BITRIX_WEBHOOK_URL: str
    WHATSAPP_TOKEN: str = ""
    CORS_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
