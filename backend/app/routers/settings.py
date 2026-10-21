from fastapi import APIRouter
from backend.app.config import settings
from backend.app.schemas import SettingsStatusResponse
from backend.app.services.ai_service import ai_service
from backend.app.services.retrieval_service import retrieval_service

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("/status", response_model=SettingsStatusResponse)
def get_settings_status():
    db_redacted = settings.database_url
    if "@" in db_redacted:
        prefix = db_redacted.split("@")[0]
        suffix = db_redacted.split("@")[1]
        scheme = prefix.split("://")[0]
        db_redacted = f"{scheme}://***:***@{suffix}"

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
            "id": settings.default_user_id,
            "name": settings.default_user_name,
            "email": settings.default_user_email
        }
    )
