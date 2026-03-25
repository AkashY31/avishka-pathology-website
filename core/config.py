"""Centralised configuration — reads from .env"""

import os
from dotenv import load_dotenv

# Load from the existing parent .env if local one is missing
_here = os.path.dirname(__file__)
_root = os.path.join(_here, "..")
load_dotenv(os.path.join(_root, ".env"), override=False)

# Try the parent project .env as fallback
_parent = os.path.join(_root, "..", "avishka-pathology-ai-final", ".env")
load_dotenv(_parent, override=False)


class Settings:
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str  = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str   = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    # Azure Speech
    AZURE_SPEECH_KEY: str    = os.getenv("AZURE_SPEECH_KEY", "")
    AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "eastus")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./avishka_pathology.db")

    # RAG
    RAG_DOCUMENTS_DIR: str = os.getenv("RAG_DOCUMENTS_DIR", "rag/documents")
    RAG_INDEX_DIR: str     = os.getenv("RAG_INDEX_DIR", "rag/index")

    # Lab Info (used in prompts)
    LAB_NAME: str    = "Avishka Pathology"
    LAB_PHONE: str   = "7355230710"
    LAB_EMAIL: str   = "avishka.pathology@outlook.com"
    LAB_ADDRESS: str = "Mahuja Modh, Martinganj, Azamgarh, U.P."
    FOUNDER: str     = "Dr. Aman Yadav (Vikas)"

    @property
    def azure_configured(self) -> bool:
        return bool(self.AZURE_OPENAI_ENDPOINT and self.AZURE_OPENAI_API_KEY)

    @property
    def speech_configured(self) -> bool:
        return bool(self.AZURE_SPEECH_KEY)


settings = Settings()
