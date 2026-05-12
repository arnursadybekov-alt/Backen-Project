from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import Parent, UserRole

_token_blacklist: set[str] = set()

bearer_scheme = HTTPBearer()




async def get_current_parent(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Parent:
    token = credentials.credentials

    if token in _token_blacklist:
        raise HTTPException(status_code=401, detail={"message": "Token has been revoked"})

    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail={"message": "Invalid token type"})

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail={"message": "Invalid token"})

    result = await db.execute(select(Parent).where(Parent.id == int(user_id)))
    parent = result.scalar_one_or_none()
    if not parent or not parent.is_active:
        raise HTTPException(status_code=401, detail={"message": "User not found or inactive"})
    return parent


async def get_current_admin(
    current_user: Parent = Depends(get_current_parent),
) -> Parent:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail={"message": "Admin access required"})
    return current_user