import logging
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
import jwt
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import User

logger = logging.getLogger(__name__)

def get_or_create_default_user(db: Session) -> User:
    user = db.query(User).filter(User.id == settings.default_user_id).first()
    if not user:
        user = User(
            id=settings.default_user_id,
            email=settings.default_user_email,
            name=settings.default_user_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Supabase authentication dependency.
    If an Authorization: Bearer <token> header is provided, it validates the Supabase JWT
    and synchronizes/retrieves the User in the database.
    If no token is supplied, it gracefully defaults to the local demo student user.
    """
    if not authorization or not authorization.strip():
        return get_or_create_default_user(db)
    
    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return get_or_create_default_user(db)
    
    token = parts[1]
    
    try:
        if settings.supabase_jwt_secret:
            # Verified decoding using Supabase project JWT Secret
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
        else:
            # Unverified claim extraction for quick development until secret is provided
            payload = jwt.decode(
                token,
                options={"verify_signature": False, "verify_aud": False}
            )
    except Exception as e:
        logger.warning(f"Failed to decode Supabase JWT token: {e}")
        # If token is invalid or expired, return 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Supabase authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    supabase_uid = payload.get("sub")
    if not supabase_uid:
        return get_or_create_default_user(db)
    
    email = payload.get("email") or f"{supabase_uid[:8]}@user.supabase"
    user_metadata = payload.get("user_metadata") or {}
    name = (
        user_metadata.get("full_name") or
        user_metadata.get("name") or
        email.split("@")[0] or
        "Student"
    )
    
    # Check if user already exists by Supabase ID or email
    user = db.query(User).filter(User.id == supabase_uid).first()
    if not user:
        user_by_email = db.query(User).filter(User.email == email).first()
        if user_by_email:
            user = user_by_email
        else:
            user = User(
                id=supabase_uid,
                email=email,
                name=name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new Supabase-authenticated user: {user.email} ({user.id})")
            
    return user
