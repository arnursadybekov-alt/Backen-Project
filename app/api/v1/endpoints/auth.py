from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import Parent, UserRole
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas.schemas import ParentRegister, LoginRequest, TokenResponse, RefreshRequest
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from fastapi.security import HTTPBearer
from app.core.dependencies import get_current_parent, bearer_scheme

security = HTTPBearer()

# In-memory blacklist (в продакшене заменить на Redis)
_token_blacklist: set[str] = set()

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: ParentRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Parent).where(Parent.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail={"message": "Email already registered"})

    parent = Parent(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.PARENT,
    )
    db.add(parent)
    await db.flush()
    await db.refresh(parent)

    token_data = {"sub": str(parent.id), "role": parent.role.value}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Parent).where(Parent.email == data.email))
    parent = result.scalar_one_or_none()
    if not parent or not verify_password(data.password, parent.hashed_password):
        raise HTTPException(status_code=401, detail={"message": "Invalid credentials"})
    if not parent.is_active:
        raise HTTPException(status_code=403, detail={"message": "Account disabled"})

    token_data = {"sub": str(parent.id), "role": parent.role.value}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail={"message": "Invalid refresh token"})

    result = await db.execute(select(Parent).where(Parent.id == int(payload["sub"])))
    parent = result.scalar_one_or_none()
    if not parent or not parent.is_active:
        raise HTTPException(status_code=401, detail={"message": "User not found"})

    token_data = {"sub": str(parent.id), "role": parent.role.value}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    _: Parent = Depends(get_current_parent),
):
    from app.core.dependencies import _token_blacklist
    _token_blacklist.add(credentials.credentials)
