# app/services/audit_service.py
import json
from datetime import datetime
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuditLog
from app.core.dependencies import get_current_admin


async def create_audit_log(
    db: AsyncSession,
    admin_id: int,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
    ip_address: Optional[str] = None,
):
    """Создать immutable audit log"""
    audit = AuditLog(
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=json.dumps(before) if before else None,
        after_state=json.dumps(after) if after else None,
        ip_address=ip_address,
        created_at=datetime.utcnow()
    )
    db.add(audit)
    await db.flush()
    return audit