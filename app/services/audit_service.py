from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import AuditLog, Parent
import json
 
 
def _serialize(obj) -> str | None:
    """Serialize a SQLAlchemy model instance to a JSON string snapshot."""
    if obj is None:
        return None
    data = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        # Convert non-serialisable types to string
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        elif hasattr(val, "value"):       # Enum
            val = val.value
        data[col.name] = val
    return json.dumps(data, ensure_ascii=False)
 
 
async def log_action(
    db: AsyncSession,
    user: Parent,
    action: str,
    resource_type: str,
    resource_id: int = None,
    details: dict = None,
    ip_address: str = None,
    before: object = None,   # model instance BEFORE change
    after: object = None,    # model instance AFTER change
):
    """
    Write an immutable audit log entry.
 
    Pass `before` with the object's state before modification,
    and `after` with the object's state after modification.
    For 'create' only `after` is needed.
    For 'delete' only `before` is needed.
    """
    entry = AuditLog(
        user_id=user.id,
        user_email=user.email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details, ensure_ascii=False) if details else None,
        before_snapshot=_serialize(before),
        after_snapshot=_serialize(after),
        ip_address=ip_address,
    )
    db.add(entry)