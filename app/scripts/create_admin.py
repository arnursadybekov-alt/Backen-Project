"""
Script to create the first admin account.
Run once after migrations:

    python scripts/create_admin.py

Reads ADMIN_EMAIL and ADMIN_PASSWORD from environment / .env file.
Falls back to interactive prompt if not set.
"""
import asyncio
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import Parent, UserRole
from app.core.security import hash_password


async def create_admin() -> None:
    email = os.getenv("ADMIN_EMAIL") or input("Admin email: ").strip()
    password = os.getenv("ADMIN_PASSWORD") or input("Admin password: ").strip()
    full_name = os.getenv("ADMIN_FULL_NAME", "Platform Admin")

    if not email or not password:
        print("ERROR: email and password are required.")
        sys.exit(1)

    if len(password) < 8:
        print("ERROR: password must be at least 8 characters.")
        sys.exit(1)

    async with AsyncSessionLocal() as session:
        existing = (await session.execute(select(Parent).where(Parent.email == email))).scalar_one_or_none()
        if existing:
            if existing.role == UserRole.ADMIN:
                print(f"Admin with email '{email}' already exists. Nothing to do.")
            else:
                # Promote existing parent to admin
                existing.role = UserRole.ADMIN
                await session.commit()
                print(f"User '{email}' promoted to ADMIN.")
            return

        admin = Parent(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        print(f"Admin account created: id={admin.id}, email={admin.email}")


if __name__ == "__main__":
    asyncio.run(create_admin())

