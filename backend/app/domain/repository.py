"""Canonical repository identity independent of HTTP and persistence frameworks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NormalizedRepository:
    provider: str
    normalized_owner: str
    normalized_name: str
    display_owner: str
    display_name: str
    canonical_url: str

    @property
    def identity(self) -> str:
        return f"{self.provider}:{self.normalized_owner}/{self.normalized_name}"

    def api_snapshot(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "identity": self.identity,
            "owner": self.display_owner,
            "name": self.display_name,
            "url": self.canonical_url,
        }
