import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "HackDataV2 Synthetic Data Platform"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    
    # OpenRouter AI Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "openai/gpt-4o-mini")
    FALLBACK_MODEL: str = os.getenv("FALLBACK_MODEL", "z-ai/glm-5.3-flash")
    
    # Defaults
    DEFAULT_LOCALE: str = "en_US"
    DEFAULT_ROW_COUNT: int = 25
    DEFAULT_SEED: int = 1337

settings = Settings()
