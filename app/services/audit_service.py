from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import AuditLog, Parent
import json


async def log_action(
    db: AsyncSession,
    user: Parent,
    action: str,
    resource_type: str,
    resource_id: int = None,
    details: dict = None,
    ip_address: str = None,
):
    entry = AuditLog(
        user_id=user.id,
        user_email=user.email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
    )
    db.add(entry)
