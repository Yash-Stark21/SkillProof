"""PostgreSQL evidence-ledger ORM models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return an aware UTC timestamp for application-side defaults."""

    return datetime.now(UTC)


class Repository(Base):
    """Last-observed identity and display metadata for a GitHub repository."""

    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "normalized_owner",
            "normalized_name",
            name="uq_repositories_normalized_identity",
        ),
        UniqueConstraint(
            "provider", "canonical_url", name="uq_repositories_provider_canonical_url"
        ),
        CheckConstraint("provider = 'github'", name="provider_github"),
        CheckConstraint(
            "normalized_owner = lower(normalized_owner) AND char_length(normalized_owner) > 0",
            name="normalized_owner_lowercase_nonempty",
        ),
        CheckConstraint(
            "normalized_name = lower(normalized_name) AND char_length(normalized_name) > 0",
            name="normalized_name_lowercase_nonempty",
        ),
        CheckConstraint(
            "provider_repository_id IS NULL OR provider_repository_id > 0",
            name="provider_repository_id_positive",
        ),
        Index(
            "uq_repositories_provider_repository_id",
            "provider",
            "provider_repository_id",
            unique=True,
            postgresql_where=text("provider_repository_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_repository_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    normalized_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        onupdate=utc_now,
        nullable=False,
    )

    scans: Mapped[list[Scan]] = relationship(back_populates="repository", passive_deletes=True)


class Scan(Base):
    """One auditable repository-analysis attempt."""

    __tablename__ = "scans"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed')", name="status_valid"
        ),
        CheckConstraint(
            "phase IN ('queued', 'resolving_repository', 'enumerating_tree', "
            "'fetching_files', 'detecting', 'persisting', 'complete', 'failed')",
            name="phase_valid",
        ),
        CheckConstraint(
            "coverage_state IS NULL OR coverage_state IN ('complete', 'partial')",
            name="coverage_state_valid",
        ),
        CheckConstraint(
            "jsonb_typeof(repository_snapshot) = 'object'",
            name="repository_snapshot_object",
        ),
        CheckConstraint(
            "jsonb_typeof(scan_policy_snapshot) = 'object'",
            name="scan_policy_snapshot_object",
        ),
        CheckConstraint(
            "jsonb_typeof(scan_policy_observations) = 'object'",
            name="scan_policy_observations_object",
        ),
        CheckConstraint("jsonb_typeof(coverage_reasons) = 'array'", name="coverage_reasons_array"),
        CheckConstraint(
            "files_discovered >= 0 AND files_inspected >= 0 "
            "AND files_skipped_by_policy >= 0 AND bytes_inspected >= 0",
            name="counters_nonnegative",
        ),
        CheckConstraint(
            "(coverage_state IS NULL AND jsonb_array_length(coverage_reasons) = 0) OR "
            "(coverage_state = 'complete' AND jsonb_array_length(coverage_reasons) = 0) OR "
            "(coverage_state = 'partial' AND jsonb_array_length(coverage_reasons) > 0)",
            name="coverage_reasons_match_state",
        ),
        CheckConstraint(
            "(status = 'queued' AND phase = 'queued' AND started_at IS NULL "
            "AND completed_at IS NULL AND coverage_state IS NULL AND failure_code IS NULL) OR "
            "(status = 'running' AND phase IN ('resolving_repository', 'enumerating_tree', "
            "'fetching_files', 'detecting', 'persisting') AND started_at IS NOT NULL "
            "AND completed_at IS NULL AND coverage_state IS NULL AND failure_code IS NULL) OR "
            "(status = 'completed' AND phase = 'complete' AND commit_sha IS NOT NULL "
            "AND coverage_state IS NOT NULL AND started_at IS NOT NULL "
            "AND completed_at IS NOT NULL AND failure_code IS NULL) OR "
            "(status = 'failed' AND phase = 'failed' AND failure_code IS NOT NULL "
            "AND completed_at IS NOT NULL AND coverage_state IS NULL)",
            name="lifecycle_consistent",
        ),
        Index("ix_scans_repository_id", "repository_id"),
        Index(
            "ix_scans_completed_result_lookup",
            "repository_id",
            "commit_sha",
            "detector_version",
            "taxonomy_version",
            "redaction_version",
            "evidence_contract_version",
            "scan_policy_version",
            "status",
        ),
        Index(
            "ix_scans_stale_active",
            "status",
            "created_at",
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    repository_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="queued", server_default="queued", nullable=False
    )
    phase: Mapped[str] = mapped_column(
        String(32), default="queued", server_default="queued", nullable=False
    )
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detector_version: Mapped[str] = mapped_column(String(32), nullable=False)
    taxonomy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    redaction_version: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_contract_version: Mapped[str] = mapped_column(String(16), nullable=False)
    scan_policy_version: Mapped[str] = mapped_column(String(16), nullable=False)
    scan_policy_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    scan_policy_observations: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    coverage_state: Mapped[str | None] = mapped_column(String(16), nullable=True)
    coverage_reasons: Mapped[list[str]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False
    )
    files_discovered: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    files_inspected: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    files_skipped_by_policy: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    bytes_inspected: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0", nullable=False
    )
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    repository: Mapped[Repository] = relationship(back_populates="scans")
    repo_files: Mapped[list[RepoFile]] = relationship(back_populates="scan", passive_deletes=True)
    evidence_items: Mapped[list[EvidenceItem]] = relationship(
        back_populates="scan", passive_deletes=True
    )


class RepoFile(Base):
    """Bounded metadata for one file discovered during a scan."""

    __tablename__ = "repo_files"
    __table_args__ = (
        UniqueConstraint("scan_id", "path", name="uq_repo_files_scan_path"),
        CheckConstraint(
            "purpose IN ('manifest', 'source', 'test', 'configuration', 'documentation', 'other')",
            name="purpose_valid",
        ),
        CheckConstraint("size_bytes >= 0", name="size_bytes_nonnegative"),
        CheckConstraint(
            "char_length(path) > 0 AND left(path, 1) <> '/' "
            "AND strpos(path, chr(92)) = 0 "
            "AND path !~ '(^|/)\\.\\.(/|$)'",
            name="path_repository_relative",
        ),
        CheckConstraint(
            "(inspected AND content_hash IS NOT NULL AND skip_reason IS NULL) OR "
            "(NOT inspected AND content_hash IS NULL AND skip_reason IS NOT NULL)",
            name="inspection_metadata_consistent",
        ),
        CheckConstraint(
            "content_hash IS NULL OR content_hash ~ '^[0-9a-f]{64}$'",
            name="content_hash_sha256",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="RESTRICT"), nullable=False
    )
    path: Mapped[str] = mapped_column(Text, nullable=False)
    git_blob_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    inspected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    skip_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )

    scan: Mapped[Scan] = relationship(back_populates="repo_files")
    evidence_items: Mapped[list[EvidenceItem]] = relationship(
        back_populates="repo_file", passive_deletes=True
    )


class EvidenceItem(Base):
    """A redacted, source-linked detector observation."""

    __tablename__ = "evidence_items"
    __table_args__ = (
        UniqueConstraint(
            "scan_id",
            "repo_file_id",
            "canonical_skill_id",
            "rule_id",
            "start_line",
            "end_line",
            name="uq_evidence_items_semantic_location",
        ),
        CheckConstraint("confidence IN ('high', 'medium', 'low')", name="confidence_valid"),
        CheckConstraint(
            "evidence_kind IN ('manifest_dependency', 'import', 'route', 'test', "
            "'component', 'hook', 'configuration', 'language_syntax', "
            "'documentation_reference')",
            name="evidence_kind_valid",
        ),
        CheckConstraint("start_line > 0 AND end_line >= start_line", name="line_range_valid"),
        CheckConstraint(
            "source_content_hash ~ '^[0-9a-f]{64}$'", name="source_content_hash_sha256"
        ),
        CheckConstraint("char_length(redacted_excerpt) > 0", name="excerpt_nonempty"),
        Index("ix_evidence_items_repo_file_id", "repo_file_id"),
        Index(
            "ix_evidence_items_scan_skill_confidence",
            "scan_id",
            "canonical_skill_id",
            "confidence",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="RESTRICT"), nullable=False
    )
    repo_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repo_files.id", ondelete="RESTRICT"), nullable=False
    )
    canonical_skill_id: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(255), nullable=False)
    detector_version: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    source_content_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    redacted_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False
    )

    scan: Mapped[Scan] = relationship(back_populates="evidence_items")
    repo_file: Mapped[RepoFile] = relationship(back_populates="evidence_items")
