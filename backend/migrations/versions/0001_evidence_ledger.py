"""Create the repository-to-evidence ledger.

Revision ID: 0001_evidence_ledger
Revises: None
Create Date: 2026-07-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_evidence_ledger"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_repository_id", sa.BigInteger(), nullable=True),
        sa.Column("normalized_owner", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("display_owner", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("default_branch", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("provider = 'github'", name="ck_repositories_provider_github"),
        sa.CheckConstraint(
            "normalized_owner = lower(normalized_owner) AND char_length(normalized_owner) > 0",
            name="ck_repositories_normalized_owner_lowercase_nonempty",
        ),
        sa.CheckConstraint(
            "normalized_name = lower(normalized_name) AND char_length(normalized_name) > 0",
            name="ck_repositories_normalized_name_lowercase_nonempty",
        ),
        sa.CheckConstraint(
            "provider_repository_id IS NULL OR provider_repository_id > 0",
            name="ck_repositories_provider_repository_id_positive",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_repositories"),
        sa.UniqueConstraint(
            "provider", "canonical_url", name="uq_repositories_provider_canonical_url"
        ),
        sa.UniqueConstraint(
            "provider",
            "normalized_owner",
            "normalized_name",
            name="uq_repositories_normalized_identity",
        ),
    )
    op.create_index(
        "uq_repositories_provider_repository_id",
        "repositories",
        ["provider", "provider_repository_id"],
        unique=True,
        postgresql_where=sa.text("provider_repository_id IS NOT NULL"),
    )

    op.create_table(
        "scans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("repository_id", sa.UUID(), nullable=False),
        sa.Column("repository_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("phase", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("detector_version", sa.String(length=32), nullable=False),
        sa.Column("taxonomy_version", sa.String(length=32), nullable=False),
        sa.Column("redaction_version", sa.String(length=32), nullable=False),
        sa.Column("evidence_contract_version", sa.String(length=16), nullable=False),
        sa.Column("scan_policy_version", sa.String(length=16), nullable=False),
        sa.Column("scan_policy_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "scan_policy_observations", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("coverage_state", sa.String(length=16), nullable=True),
        sa.Column(
            "coverage_reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("files_discovered", sa.Integer(), server_default="0", nullable=False),
        sa.Column("files_inspected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("files_skipped_by_policy", sa.Integer(), server_default="0", nullable=False),
        sa.Column("bytes_inspected", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed')",
            name="ck_scans_status_valid",
        ),
        sa.CheckConstraint(
            "phase IN ('queued', 'resolving_repository', 'enumerating_tree', "
            "'fetching_files', 'detecting', 'persisting', 'complete', 'failed')",
            name="ck_scans_phase_valid",
        ),
        sa.CheckConstraint(
            "coverage_state IS NULL OR coverage_state IN ('complete', 'partial')",
            name="ck_scans_coverage_state_valid",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(repository_snapshot) = 'object'",
            name="ck_scans_repository_snapshot_object",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(scan_policy_snapshot) = 'object'",
            name="ck_scans_scan_policy_snapshot_object",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(scan_policy_observations) = 'object'",
            name="ck_scans_scan_policy_observations_object",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(coverage_reasons) = 'array'",
            name="ck_scans_coverage_reasons_array",
        ),
        sa.CheckConstraint(
            "files_discovered >= 0 AND files_inspected >= 0 "
            "AND files_skipped_by_policy >= 0 AND bytes_inspected >= 0",
            name="ck_scans_counters_nonnegative",
        ),
        sa.CheckConstraint(
            "(coverage_state IS NULL AND jsonb_array_length(coverage_reasons) = 0) OR "
            "(coverage_state = 'complete' AND jsonb_array_length(coverage_reasons) = 0) OR "
            "(coverage_state = 'partial' AND jsonb_array_length(coverage_reasons) > 0)",
            name="ck_scans_coverage_reasons_match_state",
        ),
        sa.CheckConstraint(
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
            name="ck_scans_lifecycle_consistent",
        ),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name="fk_scans_repository_id_repositories",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_scans"),
    )
    op.create_index("ix_scans_repository_id", "scans", ["repository_id"], unique=False)
    op.create_index(
        "ix_scans_completed_result_lookup",
        "scans",
        [
            "repository_id",
            "commit_sha",
            "detector_version",
            "taxonomy_version",
            "redaction_version",
            "evidence_contract_version",
            "scan_policy_version",
            "status",
        ],
        unique=False,
    )
    op.create_index(
        "ix_scans_stale_active",
        "scans",
        ["status", "created_at"],
        unique=False,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )

    op.create_table(
        "repo_files",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("scan_id", sa.UUID(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("git_blob_sha", sa.String(length=64), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("inspected", sa.Boolean(), nullable=False),
        sa.Column("skip_reason", sa.String(length=64), nullable=True),
        sa.Column("content_hash", sa.CHAR(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "purpose IN ('manifest', 'source', 'test', 'configuration', "
            "'documentation', 'other')",
            name="ck_repo_files_purpose_valid",
        ),
        sa.CheckConstraint("size_bytes >= 0", name="ck_repo_files_size_bytes_nonnegative"),
        sa.CheckConstraint(
            "char_length(path) > 0 AND left(path, 1) <> '/' "
            "AND strpos(path, chr(92)) = 0 "
            "AND path !~ '(^|/)\\.\\.(/|$)'",
            name="ck_repo_files_path_repository_relative",
        ),
        sa.CheckConstraint(
            "(inspected AND content_hash IS NOT NULL AND skip_reason IS NULL) OR "
            "(NOT inspected AND content_hash IS NULL AND skip_reason IS NOT NULL)",
            name="ck_repo_files_inspection_metadata_consistent",
        ),
        sa.CheckConstraint(
            "content_hash IS NULL OR content_hash ~ '^[0-9a-f]{64}$'",
            name="ck_repo_files_content_hash_sha256",
        ),
        sa.ForeignKeyConstraint(
            ["scan_id"], ["scans.id"], name="fk_repo_files_scan_id_scans", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_repo_files"),
        sa.UniqueConstraint("scan_id", "path", name="uq_repo_files_scan_path"),
    )

    op.create_table(
        "evidence_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("scan_id", sa.UUID(), nullable=False),
        sa.Column("repo_file_id", sa.UUID(), nullable=False),
        sa.Column("canonical_skill_id", sa.String(length=128), nullable=False),
        sa.Column("rule_id", sa.String(length=255), nullable=False),
        sa.Column("detector_version", sa.String(length=32), nullable=False),
        sa.Column("evidence_kind", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("source_content_hash", sa.CHAR(length=64), nullable=False),
        sa.Column("redacted_excerpt", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "confidence IN ('high', 'medium', 'low')",
            name="ck_evidence_items_confidence_valid",
        ),
        sa.CheckConstraint(
            "evidence_kind IN ('manifest_dependency', 'import', 'route', 'test', "
            "'component', 'hook', 'configuration', 'language_syntax', "
            "'documentation_reference')",
            name="ck_evidence_items_evidence_kind_valid",
        ),
        sa.CheckConstraint(
            "start_line > 0 AND end_line >= start_line",
            name="ck_evidence_items_line_range_valid",
        ),
        sa.CheckConstraint(
            "source_content_hash ~ '^[0-9a-f]{64}$'",
            name="ck_evidence_items_source_content_hash_sha256",
        ),
        sa.CheckConstraint(
            "char_length(redacted_excerpt) > 0",
            name="ck_evidence_items_excerpt_nonempty",
        ),
        sa.ForeignKeyConstraint(
            ["repo_file_id"],
            ["repo_files.id"],
            name="fk_evidence_items_repo_file_id_repo_files",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["scan_id"], ["scans.id"], name="fk_evidence_items_scan_id_scans", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_evidence_items"),
        sa.UniqueConstraint(
            "scan_id",
            "repo_file_id",
            "canonical_skill_id",
            "rule_id",
            "start_line",
            "end_line",
            name="uq_evidence_items_semantic_location",
        ),
    )
    op.create_index(
        "ix_evidence_items_repo_file_id",
        "evidence_items",
        ["repo_file_id"],
        unique=False,
    )
    op.create_index(
        "ix_evidence_items_scan_skill_confidence",
        "evidence_items",
        ["scan_id", "canonical_skill_id", "confidence"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_evidence_items_scan_skill_confidence", table_name="evidence_items")
    op.drop_index("ix_evidence_items_repo_file_id", table_name="evidence_items")
    op.drop_table("evidence_items")
    op.drop_table("repo_files")
    op.drop_index("ix_scans_stale_active", table_name="scans")
    op.drop_index("ix_scans_completed_result_lookup", table_name="scans")
    op.drop_index("ix_scans_repository_id", table_name="scans")
    op.drop_table("scans")
    op.drop_index("uq_repositories_provider_repository_id", table_name="repositories")
    op.drop_table("repositories")
