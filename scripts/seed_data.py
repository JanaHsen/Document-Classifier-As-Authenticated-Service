#!/usr/bin/env python
"""Seed the database with sample data for testing and development.

This script populates all tables with realistic sample data:
- Users (admin, reviewer, auditor) with real bcrypt password hashes
- Batches (various states)
- Predictions (linked to batches)
- Audit logs (tracking user actions)

Usage:
    python scripts/seed_data.py

Environment:
    Requires DATABASE_URL or .env file to be configured.
    Set DATABASE_URL to your database connection string.
    For SQLite: "sqlite+aiosqlite:///./test.db"
    For PostgreSQL: "postgresql+asyncpg://user:pass@host/dbname"
"""

import asyncio
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import User, Batch, Prediction, AuditLog
from app.core.constants import Role, BatchStatus, AuditAction
from app.core.config import settings

# Import bcrypt for password hashing
import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ─────────────────────────────────────────────────────────────────────────────
# Sample data definitions
# ─────────────────────────────────────────────────────────────────────────────

# Pre-hashed passwords for seed users
ADMIN_PASSWORD = "AdminPass123!"
REVIEWER_PASSWORD = "ReviewerPass123!"
AUDITOR_PASSWORD = "AuditorPass123!"

USERS = [
    {
        "email": "admin@example.com",
        "hashed_password": hash_password(ADMIN_PASSWORD),
        "role": Role.ADMIN,
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
    },
    {
        "email": "reviewer1@example.com",
        "hashed_password": hash_password(REVIEWER_PASSWORD),
        "role": Role.REVIEWER,
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
    },
    {
        "email": "reviewer2@example.com",
        "hashed_password": hash_password(REVIEWER_PASSWORD),
        "role": Role.REVIEWER,
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
    },
    {
        "email": "auditor@example.com",
        "hashed_password": hash_password(AUDITOR_PASSWORD),
        "role": Role.AUDITOR,
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
    },
]

BATCHES = [
    {"state": BatchStatus.PENDING, "created_at": datetime.utcnow() - timedelta(days=5)},
    {"state": BatchStatus.PROCESSING, "created_at": datetime.utcnow() - timedelta(days=4)},
    {"state": BatchStatus.COMPLETE, "created_at": datetime.utcnow() - timedelta(days=3)},
    {"state": BatchStatus.FAILED, "created_at": datetime.utcnow() - timedelta(days=2)},
    {"state": BatchStatus.COMPLETE, "created_at": datetime.utcnow() - timedelta(days=1)},
]

# predictions count per batch
PREDICTIONS_PER_BATCH = [3, 2, 1, 0, 0]

PREDICTION_LABELS = [
    "cat", "dog", "bird", "car", "truck", "bicycle", "person",
    "traffic light", "stop sign", "parking meter"
]

OVERLAY_PATHS = [
    "/overlays/batch1/pred1.png",
    "/overlays/batch1/pred2.png",
    "/overlays/batch1/pred3.png",
    "/overlays/batch2/pred1.png",
    "/overlays/batch2/pred2.png",
    "/overlays/batch3/pred1.png",
]


# ─────────────────────────────────────────────────────────────────────────────
# Seeding logic
# ─────────────────────────────────────────────────────────────────────────────

async def clear_tables(session: AsyncSession):
    """Delete all rows from all tables (FK-safe order)."""
    print("Clearing existing data...")
    # Delete in child-first order (audit_logs references users and predictions)
    await session.execute(delete(AuditLog))
    await session.execute(delete(Prediction))
    await session.execute(delete(Batch))
    await session.execute(delete(User))
    await session.flush()
    print("  Tables cleared.")


async def seed_users(session: AsyncSession) -> dict[int, User]:
    """Create users and return mapping of id -> User object."""
    print("Seeding users...")
    users = []
    for user_data in USERS:
        try:
            user = User(**user_data)
            session.add(user)
            users.append(user)
        except Exception as e:
            print(f"  ERROR creating user {user_data.get('email')}: {e}")
            raise
    await session.flush()
    for user in users:
        await session.refresh(user)
    print(f"  Created {len(users)} users: IDs={[u.id for u in users]}")
    return {u.id: u for u in users}


async def seed_batches(session: AsyncSession) -> dict[int, Batch]:
    """Create batches and return mapping of id -> Batch object."""
    print("Seeding batches...")
    batches = []
    for i, batch_data in enumerate(BATCHES):
        try:
            batch = Batch(**batch_data)
            session.add(batch)
            batches.append(batch)
        except Exception as e:
            print(f"  ERROR creating batch {i}: {e}")
            raise
    await session.flush()
    for batch in batches:
        await session.refresh(batch)
    print(f"  Created {len(batches)} batches: IDs={[b.id for b in batches]}")
    return {b.id: b for b in batches}


async def seed_predictions(session: AsyncSession, batches: dict[int, Batch]) -> list[Prediction]:
    """Create predictions for batches according to PREDICTIONS_PER_BATCH."""
    print("Seeding predictions...")
    predictions = []
    overlay_idx = 0
    for batch_idx, (batch_id, batch) in enumerate(batches.items()):
        num_preds = PREDICTIONS_PER_BATCH[batch_idx]
        for i in range(num_preds):
            label = PREDICTION_LABELS[(batch_idx * 3 + i) % len(PREDICTION_LABELS)]
            # Create a mix of low and high confidence predictions
            # First prediction in each batch gets low confidence (< 0.7)
            if i == 0:
                confidence = round(0.50 + (i * 0.05), 2)  # 0.50, 0.55, etc.
            else:
                confidence = round(0.70 + (i * 0.08), 2)
            overlay_path = OVERLAY_PATHS[overlay_idx % len(OVERLAY_PATHS)]
            overlay_idx += 1
            try:
                pred = Prediction(
                    batch_id=batch_id,
                    label=label,
                    confidence=confidence,
                    overlay_path=overlay_path,
                )
                session.add(pred)
                predictions.append(pred)
            except Exception as e:
                print(f"  ERROR creating prediction for batch {batch_id}: {e}")
                raise
    await session.flush()
    for pred in predictions:
        await session.refresh(pred)
    print(f"  Created {len(predictions)} predictions: IDs={[p.id for p in predictions]}")
    # Print confidence values for debugging
    confidences = [p.confidence for p in predictions]
    print(f"  Confidences: {confidences}")
    return predictions


async def seed_audit_logs(
    session: AsyncSession,
    users: dict[int, User],
    batches: dict[int, Batch],
    predictions: list[Prediction],
):
    """Create audit logs for user actions."""
    print("Seeding audit logs...")
    logs = []

    # Find admin and reviewer users by role
    admin = next((u for u in users.values() if u.role == Role.ADMIN), None)
    reviewer = next((u for u in users.values() if u.role == Role.REVIEWER), None)

    if not admin or not reviewer:
        raise ValueError("Could not find admin or reviewer user")

    print(f"  Admin user ID: {admin.id}, Reviewer user ID: {reviewer.id}")

    # Role change audit
    logs.append(AuditLog(
        actor_id=admin.id,
        action=AuditAction.CHANGE_ROLE,
        target_type="user",
        target_id=reviewer.id,
        old_value={"role": "reviewer"},
        new_value={"role": "reviewer"},
        timestamp=datetime.utcnow() - timedelta(days=4),
    ))

    # Batch state change audits
    for batch_id, batch in batches.items():
        logs.append(AuditLog(
            actor_id=admin.id,
            action=AuditAction.CHANGE_STATE,
            target_type="batch",
            target_id=batch.id,
            old_value={"state": "pending"},
            new_value={"state": batch.state.value},
            timestamp=batch.created_at,
        ))

    # Relabel audits for each prediction
    for pred in predictions:
        old_label = "unlabeled"
        new_label = pred.label
        logs.append(AuditLog(
            actor_id=reviewer.id,
            action=AuditAction.RELABEL_PRED,
            target_type="prediction",
            target_id=pred.id,
            old_value={"label": old_label},
            new_value={"label": new_label},
            timestamp=pred.created_at + timedelta(minutes=5),
        ))

    try:
        session.add_all(logs)
        await session.flush()
        print(f"  Created {len(logs)} audit log entries ({len(predictions)} relabel entries)")
    except Exception as e:
        print(f"  ERROR creating audit logs: {e}")
        for i, log in enumerate(logs):
            print(f"    Log {i}: actor={log.actor_id}, action={log.action}, target={log.target_type}:{log.target_id}")
        raise


async def main():
    """Main seeding entrypoint."""
    database_url = settings.DATABASE_URL or settings.DATABASE_SYNC_URL
    print(f"Using database: {database_url}")

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
    )

    # Ensure tables exist (and clear first for idempotency)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                # Clear existing data
                await clear_tables(session)

                # Seed in order respecting FK dependencies
                users = await seed_users(session)
                batches = await seed_batches(session)
                predictions = await seed_predictions(session, batches)
                await seed_audit_logs(session, users, batches, predictions)

            await session.commit()
            print("\nAll data seeded successfully!")
            print(f"   Users: {len(users)} (admin: {next(u.id for u in users.values() if u.role == Role.ADMIN)}, "
                  f"reviewer: {next(u.id for u in users.values() if u.role == Role.REVIEWER)}, "
                  f"auditor: {next(u.id for u in users.values() if u.role == Role.AUDITOR)})")
            print(f"   Batches: {len(batches)} (states: {[b.state.value for b in batches.values()]})")
            print(f"   Predictions: {len(predictions)}")
            print("\nPre-seeded user credentials:")
            print(f"   Admin:     {ADMIN_PASSWORD}")
            print(f"   Reviewer:  {REVIEWER_PASSWORD}")
            print(f"   Auditor:   {AUDITOR_PASSWORD}")
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            traceback.print_exc()
            await session.rollback()
            raise

    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        sys.exit(1)
