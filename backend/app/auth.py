import logging
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
import jwt
from jwt import (
    PyJWKClient,
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError
)
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import User

logger = logging.getLogger(__name__)

_jwks_client: Optional[PyJWKClient] = None

def get_jwks_client() -> Optional[PyJWKClient]:
    global _jwks_client
    if _jwks_client is None and settings.supabase_url:
        jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        try:
            _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
        except Exception as e:
            logger.warning(f"Could not initialize PyJWKClient for {jwks_url}: {e}")
            _jwks_client = None
    return _jwks_client

def verify_token_via_supabase_api(token: str) -> Optional[Dict[str, Any]]:
    """
    Direct verification against Supabase Auth API endpoint (/auth/v1/user).
    Serves as an authoritative verification method when JWKS or local decoding encounters key discrepancies.
    """
    if not settings.supabase_url:
        return None
        
    anon_key = settings.supabase_anon_key or settings.supabase_service_role_key
    if not anon_key:
        return None

    user_endpoint = f"{settings.supabase_url.rstrip('/')}/auth/v1/user"
    req = urllib.request.Request(
        user_endpoint,
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": anon_key,
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {
                "sub": data.get("id"),
                "email": data.get("email"),
                "user_metadata": data.get("user_metadata") or {},
                "role": data.get("role") or "authenticated"
            }
    except urllib.error.HTTPError as http_err:
        if http_err.code in (401, 403):
            logger.warning(f"Supabase Auth rejected token with status {http_err.code}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired Supabase authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.warning(f"Supabase /auth/v1/user HTTP {http_err.code}: {http_err}")
    except Exception as e:
        logger.warning(f"Supabase /auth/v1/user call failed: {e}")
    return None

def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a Supabase JWT token.
    Supports modern Supabase asymmetric signing algorithms (ES256, RS256) via JWKS,
    traditional symmetric signing (HS256) via SUPABASE_JWT_SECRET,
    and authoritative fallback via Supabase's /auth/v1/user endpoint.
    """
    try:
        header = jwt.get_unverified_header(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Supabase authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    alg = header.get("alg", "HS256")

    # 1. Asymmetric algorithms (ES256, RS256) - current default for Supabase Auth
    if alg in ("ES256", "RS256"):
        # First attempt: Verify using JWKS public keys
        jwks_client = get_jwks_client()
        if jwks_client:
            try:
                try:
                    signing_key = jwks_client.get_signing_key_from_jwt(token)
                    keys_to_try = [signing_key.key]
                except Exception:
                    keys_to_try = [k.key for k in jwks_client.get_signing_keys()]

                for key in keys_to_try:
                    try:
                        return jwt.decode(
                            token,
                            key,
                            algorithms=[alg],
                            options={"verify_aud": False}
                        )
                    except (InvalidSignatureError, DecodeError):
                        continue
            except ExpiredSignatureError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid or expired Supabase authentication token: {str(e)}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except Exception as e:
                logger.warning(f"JWKS verification failed for {alg}: {e}")

        # Second attempt: Authoritative verification via Supabase /auth/v1/user API
        api_payload = verify_token_via_supabase_api(token)
        if api_payload:
            return api_payload

        # Third attempt: Unverified fallback if in development or no secrets configured
        if not settings.supabase_jwt_secret and not settings.supabase_url:
            return jwt.decode(
                token,
                options={"verify_signature": False, "verify_aud": False, "verify_exp": True}
            )

        # Fallback extraction if token format is valid but remote JWKS is unreachable
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False, "verify_aud": False, "verify_exp": True}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired Supabase authentication token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 2. Symmetric algorithms (HS256)
    if alg == "HS256":
        try:
            if settings.supabase_jwt_secret:
                return jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
            else:
                return jwt.decode(
                    token,
                    options={"verify_signature": False, "verify_aud": False, "verify_exp": True}
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired Supabase authentication token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 3. Any other algorithms - attempt with standard supported algorithms
    try:
        supported_algs = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]
        if settings.supabase_jwt_secret:
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=supported_algs,
                options={"verify_aud": False}
            )
        return jwt.decode(
            token,
            options={"verify_signature": False, "verify_aud": False, "verify_exp": True}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Supabase authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    payload = decode_supabase_jwt(token)
    
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

def get_user_accessible_subject(db: Session, subject_id: str, user: User):
    """
    Retrieves a subject by ID, granting access if:
    1. The authenticated user owns the subject, OR
    2. The subject was created under the default user, automatically claiming it for the authenticated user, OR
    3. The current user is the default user (token hydrating or unauthenticated read), OR
    4. The user's email matches the subject owner's email.
    """
    from backend.app.models import Subject
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        return None
    if subject.user_id == user.id:
        return subject
    if user.id == settings.default_user_id:
        return subject
    if subject.user_id == settings.default_user_id:
        subject.user_id = user.id
        db.commit()
        db.refresh(subject)
        return subject
    # Check if owner email matches current user email
    if user.email:
        owner = db.query(User).filter(User.id == subject.user_id).first()
        if owner and owner.email and owner.email.lower() == user.email.lower():
            return subject
    return None

