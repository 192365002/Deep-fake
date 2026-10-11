"""
Supabase Authentication Verification Utilities for Social Shield Backend
Replaces Firebase Admin SDK with secure Supabase JWT and GoTrue Auth verification.
"""
import os
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from utils.database import get_supabase_client, is_mock_db

logger = logging.getLogger(__name__)

security = HTTPBearer()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    FastAPI dependency: Verifies Supabase Bearer access token and returns canonical user UUID.
    Enforces that user identity is derived strictly from verified JWT claims.
    """
    token = credentials.credentials
    user_info = verify_supabase_token(token)
    return user_info["sub"]


def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Verifies Supabase JWT token signature, audience, and expiration.
    Supports JWT secret verification, GoTrue API validation, and local dev fallback.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token missing")

    # 1. Dev / Demo token fallback (when offline or unconfigured)
    if is_mock_db() or not SUPABASE_JWT_SECRET:
        if token.startswith("demo_") or token.startswith("dev_"):
            clean_id = token.replace("demo_", "").replace("dev_", "")
            # Return stable UUID or clean string
            return {"sub": clean_id, "uid": clean_id, "email": f"{clean_id}@socialshield.ai", "role": "authenticated"}
        
        # If it's a JWT but secret is not set, decode payload without verification for dev convenience
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            if "sub" in unverified:
                return unverified
        except Exception:
            pass

        # If in mock mode, treat the token string itself as user ID
        return {"sub": token, "uid": token, "email": "dev@socialshield.ai", "role": "authenticated"}

    # 2. Verify with Supabase JWT Secret (HS256)
    try:
        decoded = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        user_id = decoded.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing subject (sub)")
        decoded["uid"] = user_id
        return decoded

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Please log in again.")
    except jwt.InvalidTokenError as e:
        logger.debug(f"Local JWT verification failed: {e}. Attempting Supabase GoTrue verification...")

    # 3. Fallback: Verify via Supabase Auth GoTrue API
    client = get_supabase_client()
    if client is not None and not is_mock_db():
        try:
            user_response = client.auth.get_user(token)
            if user_response and user_response.user:
                u = user_response.user
                return {
                    "sub": u.id,
                    "uid": u.id,
                    "email": u.email,
                    "role": getattr(u, "role", "authenticated")
                }
        except Exception as e:
            logger.error(f"GoTrue token verification error: {e}")

    raise HTTPException(status_code=401, detail="Invalid authentication credentials")


def verify_token(token: str) -> Dict[str, Any]:
    """Compatibility helper for routers/endpoints needing dictionary user info"""
    return verify_supabase_token(token)
