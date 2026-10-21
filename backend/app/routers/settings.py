from fastapi import APIRouter, Depends
from backend.app.config import settings
from backend.app.schemas import SettingsStatusResponse
from backend.app.services.ai_service import ai_service
from backend.app.services.retrieval_service import retrieval_service
from backend.app.auth import get_current_user
from backend.app.models import User

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("/status", response_model=SettingsStatusResponse)
def get_settings_status(user: User = Depends(get_current_user)):
    db_redacted = settings.database_url
    if "@" in db_redacted:
        prefix = db_redacted.split("@")[0]
        suffix = db_redacted.split("@")[1]
        scheme = prefix.split("://")[0]
        db_redacted = f"{scheme}://***:***@{suffix}"

    is_supabase_db = "supabase" in settings.database_url.lower() or "pooler.supabase" in settings.database_url.lower()
    is_supabase_configured = bool(settings.supabase_url or settings.supabase_anon_key or is_supabase_db)
    
    supabase_url_redacted = None
    if settings.supabase_url:
        supabase_url_redacted = settings.supabase_url.split("//")[-1]

    return SettingsStatusResponse(
        app_name=settings.app_name,
        app_env=settings.app_env,
        demo_mode=settings.demo_mode,
        live_ai_available=ai_service.is_live_mode,
        nebius_base_url=settings.openrouter_base_url,
        nebius_fast_model=settings.openrouter_fast_model,
        nebius_reasoning_model=settings.openrouter_reasoning_model,
        embedding_provider=retrieval_service.active_mode,
        storage_dir=str(settings.storage_dir),
        database_url_redacted=db_redacted,
        active_user={
            "id": user.id,
            "name": user.name,
            "email": user.email
        },
        supabase_configured=is_supabase_configured,
        supabase_db_connected=is_supabase_db,
        supabase_url_redacted=supabase_url_redacted
    )
