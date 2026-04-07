from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import settings

security = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class AuthenticatedUser:
    id: str
    email: str | None
    access_token: str


@lru_cache(maxsize=1)
def get_jwks_client() -> PyJWKClient:
    if not settings.supabase_url:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured",
        )
    return PyJWKClient(
        f"{settings.supabase_url}/auth/v1/.well-known/jwks.json",
        cache_keys=True,
        lifespan=3600,
    )


def decode_jwt(token: str) -> dict[str, object]:
    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="authenticated",
            issuer=f"{settings.supabase_url}/auth/v1",
        )
        return dict(payload)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token has expired") from exc
    except (
        jwt.InvalidAudienceError,
        jwt.InvalidIssuerError,
        jwt.InvalidTokenError,
        jwt.PyJWKClientError,
    ) as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    except jwt.PyJWKClientConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail="Authentication service unavailable",
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_jwt(credentials.credentials)
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    email = payload.get("email")
    return AuthenticatedUser(
        id=user_id,
        email=email if isinstance(email, str) else None,
        access_token=credentials.credentials,
    )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthenticatedUser | None:
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
