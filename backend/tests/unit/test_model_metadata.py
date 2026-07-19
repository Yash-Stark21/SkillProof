"""Static SQLAlchemy schema tests that do not require PostgreSQL."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.db.models import EvidenceItem, RepoFile, Repository, Scan


def _unique_column_sets(table: object) -> set[frozenset[str]]:
    constraints: Iterable[object] = table.constraints  # type: ignore[attr-defined]
    return {
        frozenset(constraint.columns.keys())
        for constraint in constraints
        if isinstance(constraint, UniqueConstraint)
    }


def _index_column_sets(table: object) -> set[tuple[str, ...]]:
    indexes: Iterable[Index] = table.indexes  # type: ignore[attr-defined]
    return {tuple(index.columns.keys()) for index in indexes}


def _check_sql(table: object) -> str:
    constraints: Iterable[object] = table.constraints  # type: ignore[attr-defined]
    return " ".join(
        str(constraint.sqltext).lower()
        for constraint in constraints
        if isinstance(constraint, CheckConstraint)
    )


def test_evidence_ledger_declares_only_the_first_increment_tables() -> None:
    assert set(Base.metadata.tables) == {
        "repositories",
        "scans",
        "repo_files",
        "evidence_items",
    }
    assert Repository.__table__.name == "repositories"
    assert Scan.__table__.name == "scans"
    assert RepoFile.__table__.name == "repo_files"
    assert EvidenceItem.__table__.name == "evidence_items"


def test_repository_identity_has_canonical_and_provider_uniqueness() -> None:
    table = Repository.__table__
    assert frozenset({"provider", "normalized_owner", "normalized_name"}) in _unique_column_sets(
        table
    )
    assert {
        "id",
        "provider",
        "provider_repository_id",
        "normalized_owner",
        "normalized_name",
        "display_owner",
        "display_name",
        "canonical_url",
        "default_branch",
        "created_at",
        "updated_at",
    } == set(table.columns.keys())

    provider_id_indexes = [
        index
        for index in table.indexes
        if tuple(index.columns.keys()) == ("provider", "provider_repository_id")
    ]
    assert len(provider_id_indexes) == 1
    assert provider_id_indexes[0].unique is True
    assert provider_id_indexes[0].dialect_options["postgresql"].get("where") is not None


def test_scan_keeps_an_immutable_repository_and_policy_snapshot() -> None:
    table = Scan.__table__
    assert {
        "repository_snapshot",
        "scan_policy_snapshot",
        "scan_policy_observations",
        "coverage_reasons",
    }.issubset(table.columns.keys())
    for column_name in (
        "repository_snapshot",
        "scan_policy_snapshot",
        "scan_policy_observations",
        "coverage_reasons",
    ):
        assert isinstance(table.c[column_name].type, JSONB)
        assert table.c[column_name].nullable is False

    checks = _check_sql(table)
    for keyword in (
        "queued",
        "running",
        "completed",
        "failed",
        "coverage_state",
        "coverage_reasons",
        "files_discovered",
        "files_inspected",
        "files_skipped_by_policy",
        "bytes_inspected",
    ):
        assert keyword in checks

    assert (
        "repository_id",
        "commit_sha",
        "detector_version",
        "taxonomy_version",
        "redaction_version",
        "evidence_contract_version",
        "scan_policy_version",
        "status",
    ) in _index_column_sets(table)


def test_repo_file_state_is_database_constrained() -> None:
    table = RepoFile.__table__
    assert frozenset({"scan_id", "path"}) in _unique_column_sets(table)
    checks = _check_sql(table)
    for keyword in ("size_bytes", "inspected", "skip_reason", "content_hash"):
        assert keyword in checks
    assert "content" not in table.columns.keys()
    assert "raw_content" not in table.columns.keys()


def test_evidence_has_provenance_constraints_without_persisted_eligibility() -> None:
    table = EvidenceItem.__table__
    assert frozenset(
        {
            "scan_id",
            "repo_file_id",
            "canonical_skill_id",
            "rule_id",
            "start_line",
            "end_line",
        }
    ) in _unique_column_sets(table)
    assert (
        "scan_id",
        "canonical_skill_id",
        "confidence",
    ) in _index_column_sets(table)
    assert "claim_eligible" not in table.columns.keys()
    assert "source_content" not in table.columns.keys()
    checks = _check_sql(table)
    for keyword in ("start_line", "end_line", "redacted_excerpt"):
        assert keyword in checks


def test_provenance_foreign_keys_are_restrictive() -> None:
    foreign_keys: list[ForeignKey] = [
        next(iter(Scan.__table__.c.repository_id.foreign_keys)),
        next(iter(RepoFile.__table__.c.scan_id.foreign_keys)),
        next(iter(EvidenceItem.__table__.c.scan_id.foreign_keys)),
        next(iter(EvidenceItem.__table__.c.repo_file_id.foreign_keys)),
    ]
    assert all(foreign_key.ondelete == "RESTRICT" for foreign_key in foreign_keys)


def test_enums_are_readable_constrained_strings_and_timestamps_are_aware() -> None:
    for table in Base.metadata.sorted_tables:
        for column in table.columns:
            assert not isinstance(column.type, Enum)
            if column.name.endswith("_at"):
                assert isinstance(column.type, DateTime)
                assert column.type.timezone is True
