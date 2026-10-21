import os
from pydantic import BaseModel
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    app_name: str = "ExamLoop API"
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'examloop.db'}")
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage")))
    
    # OpenRouter AI / NVIDIA Nemotron Configuration
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Model hierarchy:
    # 1st Priority: NVIDIA Nemotron 3.5 Lightning (Free tier verified 100% JSON)
    # Fallbacks: Minimax / Google Gemma free models
    openrouter_fast_model: str = os.getenv("OPENROUTER_FAST_MODEL", "nvidia/nemotron-3.5-lightning:free")
    openrouter_reasoning_model: str = os.getenv("OPENROUTER_REASONING_MODEL", "nvidia/nemotron-3.5-lightning:free")
    openrouter_fallback_model: str = os.getenv("OPENROUTER_FALLBACK_MODEL", "minimax/minimax-m3.1-flash:free")

    # Embeddings / Retrieval
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "lexical")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "none")
    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
    
    # Demo Mode: false when live API key is available
    demo_mode: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
    
    default_user_id: str = "usr_default_01"
    default_user_email: str = "student@examloop.local"
    default_user_name: str = "Demo Student"
    
    max_upload_size_bytes: int = 15 * 1024 * 1024 # 15MB
    allowed_mime_types: list[str] = ["application/pdf", "text/plain"]

settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
