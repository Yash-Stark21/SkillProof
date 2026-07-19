"""Database readiness check kept separate for dependency overrides."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


class DatabaseReadinessService:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def check(self) -> bool:
        try:
            async with self.engine.connect() as connection:
                value = await connection.scalar(text("SELECT 1"))
                return bool(value == 1)
        except Exception:
            return False
