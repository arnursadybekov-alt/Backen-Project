# app/services/audit_service.py
import json
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuditLog


async def create_audit_log(
    db: AsyncSession,
    admin_id: int,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    before: Optional[Dict] = None,
    after: Optional[Dict] = None,
    ip_address: Optional[str] = None,
):
    """Immutable audit log with before/after snapshots"""
    audit = AuditLog(
        admin_id=admin_id,
        action=action.upper(),
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=json.dumps(before, ensure_ascii=False, default=str) if before else None,
        after_state=json.dumps(after, ensure_ascii=False, default=str) if after else None,
        ip_address=ip_address,
        created_at=datetime.utcnow(),
    )
    db.add(audit)
    await db.commit()
    return audit