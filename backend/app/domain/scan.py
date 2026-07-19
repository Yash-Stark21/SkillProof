"""Domain vocabulary for repository scans and evidence."""

from __future__ import annotations

from enum import StrEnum


class ScanStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanPhase(StrEnum):
    QUEUED = "queued"
    RESOLVING_REPOSITORY = "resolving_repository"
    ENUMERATING_TREE = "enumerating_tree"
    FETCHING_FILES = "fetching_files"
    DETECTING = "detecting"
    PERSISTING = "persisting"
    COMPLETE = "complete"
    FAILED = "failed"


class CoverageState(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"


class FilePurpose(StrEnum):
    MANIFEST = "manifest"
    SOURCE = "source"
    TEST = "test"
    CONFIGURATION = "configuration"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


EVIDENCE_KINDS = frozenset(
    {
        "manifest_dependency",
        "import",
        "route",
        "test",
        "component",
        "hook",
        "configuration",
        "language_syntax",
        "documentation_reference",
    }
)

CLAIM_ELIGIBLE_CONFIDENCE = frozenset({Confidence.HIGH, Confidence.MEDIUM})
