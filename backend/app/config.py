import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

# Load .env from workspace root, falling back to BASE_DIR / '.env'
if (ROOT_DIR / ".env").exists():
    load_dotenv(ROOT_DIR / ".env")
elif (BASE_DIR / ".env").exists():
    load_dotenv(BASE_DIR / ".env")
else:
    load_dotenv()

class Settings(BaseModel):
    app_name: str = "ExamLoop API"
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'examloop.db'}")
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage")))
    
    # OmniRoute & OpenRouter Gateway Configuration
    omniroute_api_key: str = os.getenv("OMNIROUTE_API_KEY", "")
    omniroute_base_url: str = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")

    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Specialized Model Configuration Per Task:
    # 1. Topic Extraction: High speed, clean JSON output
    model_topic_extraction: str = os.getenv("MODEL_TOPIC_EXTRACTION", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free")
    # 2. Test Generation: 550B MoE deep rubric & question synthesis
    model_test_generation: str = os.getenv("MODEL_TEST_GENERATION", "nvidia/nemotron-3-ultra-550b-a55b:free")
    # 3. Answer Evaluation & Grading: Precise rubric scoring and misconception diagnosis
    model_evaluation: str = os.getenv("MODEL_EVALUATION", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free")

    openrouter_fast_model: str = os.getenv("OPENROUTER_FAST_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free")
    openrouter_reasoning_model: str = os.getenv("OPENROUTER_REASONING_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
    openrouter_fallback_model: str = os.getenv("OPENROUTER_FALLBACK_MODEL", "openrouter/free")

    # Embeddings / Retrieval
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "lexical")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "none")
    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
    
    # Demo Mode: false when live API key is available
    demo_mode: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
    
    # Supabase Configuration
    supabase_url: str = os.getenv("SUPABASE_URL", os.getenv("NEXT_PUBLIC_SUPABASE_URL", ""))
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", ""))
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    default_user_id: str = "usr_default_01"
    default_user_email: str = "student@examloop.local"
    default_user_name: str = "Demo Student"
    
    max_upload_size_bytes: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(100 * 1024 * 1024))) # 100MB default
    allowed_mime_types: list[str] = ["application/pdf", "text/plain"]

settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
