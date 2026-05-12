from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.user import Parent, Child, Badge
from app.models.curriculum import LessonProgress, ExerciseResult
from app.core.dependencies import get_current_parent, get_current_admin
from app.schemas.schemas import ChildCreate, ChildUpdate, ChildOut, BadgeOut, LessonProgressOut, PaginatedResponse

router = APIRouter(prefix="/children", tags=["Children"])


def _check_child_owner(child: Child, current_user: Parent):
    if child.parent_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail={"message": "Access denied"})


@router.get("", response_model=PaginatedResponse)
async def list_children(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    query = select(Child).where(Child.parent_id == current_user.id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return PaginatedResponse(
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        items=[ChildOut.model_validate(c) for c in result.scalars().all()],
    )


@router.post("", response_model=ChildOut, status_code=status.HTTP_201_CREATED)
async def create_child(
    data: ChildCreate,
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    child = Child(parent_id=current_user.id, **data.model_dump())
    db.add(child)
    await db.flush()
    await db.refresh(child)
    return child


@router.get("/{child_id}", response_model=ChildOut)
async def get_child(
    child_id: int,
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Child).where(Child.id == child_id))
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail={"message": "Child not found"})
    _check_child_owner(child, current_user)
    return child


@router.put("/{child_id}", response_model=ChildOut)
async def update_child(
    child_id: int,
    data: ChildUpdate,
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Child).where(Child.id == child_id))
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail={"message": "Child not found"})
    _check_child_owner(child, current_user)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(child, field, value)
    await db.flush()
    await db.refresh(child)
    return child


@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
    child_id: int,
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Child).where(Child.id == child_id))
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail={"message": "Child not found"})
    _check_child_owner(child, current_user)
    await db.delete(child)


@router.get("/{child_id}/badges", response_model=list[BadgeOut])
async def get_child_badges(
    child_id: int,
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Child).where(Child.id == child_id))
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail={"message": "Child not found"})
    _check_child_owner(child, current_user)
    badges = await db.execute(select(Badge).where(Badge.child_id == child_id))
    return badges.scalars().all()


@router.get("/{child_id}/progress", response_model=PaginatedResponse)
async def get_child_progress(
    child_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Child).where(Child.id == child_id))
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail={"message": "Child not found"})
    _check_child_owner(child, current_user)

    query = select(LessonProgress).where(LessonProgress.child_id == child_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    records = await db.execute(
        query.order_by(LessonProgress.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return PaginatedResponse(
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        items=[LessonProgressOut.model_validate(r) for r in records.scalars().all()],
    )
