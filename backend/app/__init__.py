"""SkillProof backend application package."""

from __future__ import annotations

import asyncio
import sys


def _configure_asyncio_runtime() -> None:
    """Use the event loop required by psycopg async connections on Windows."""

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


_configure_asyncio_runtime()

__version__ = "0.1.0"
