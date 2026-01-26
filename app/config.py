import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    SHEET_URL = os.getenv("SHEET_URL")
    WEAVIATE_URL = os.getenv("WEAVIATE_ENDPOINT")
    WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")


settings = Settings()
