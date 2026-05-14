#!/usr/bin/env python
"""Reset database: drop all tables, recreate, and seed."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import async_engine, Base
from app.core.config import settings
from dotenv import load_dotenv

# Load .env
load_dotenv(Path(__file__).parent.parent / ".env")

async def reset_db():
    print(f"Connecting to: {settings.DATABASE_URL}")
    async with async_engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Database schema reset complete.")

if __name__ == "__main__":
    asyncio.run(reset_db())
