from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    SHEET_URL: str
    WEAVIATE_URL: str
    WEAVIATE_API_KEY: str
    GOOGLE_KEY_PATH: str | None = None
    MODEL: str = "openai/gpt-4o"

    model_config = SettingsConfigDict(
        frozen=True,
    )

settings = Settings()
