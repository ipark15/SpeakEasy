from __future__ import annotations
import os
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")

_security = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _jwks_client():
    import jwt
    return jwt.PyJWKClient(
        f"https://{AUTH0_DOMAIN}/.well-known/jwks.json",
        cache_keys=True,
    )


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> dict:
    """FastAPI dependency — returns the decoded JWT payload.

    Falls back to a dev-user dict when AUTH0_DOMAIN is not configured so
    the backend still works without Auth0 during local development.
    """
    if not AUTH0_DOMAIN or not AUTH0_AUDIENCE:
        return {"sub": "dev-user"}

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    import jwt

    try:
        client = _jwks_client()
        signing_key = client.get_signing_key_from_jwt(credentials.credentials)
        payload = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
