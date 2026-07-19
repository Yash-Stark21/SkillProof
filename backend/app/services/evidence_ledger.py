"""Validate detector output before any evidence value reaches persistence."""

from __future__ import annotations

import re
from uuid import UUID

from app.domain.ledger import CompletedScanLedger
from app.domain.ports import EvidenceLedgerStore
from app.domain.scan import EVIDENCE_KINDS, Confidence, FilePurpose

_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class EvidenceContractError(ValueError):
    pass


class EvidenceLedgerService:
    def __init__(self, store: EvidenceLedgerStore) -> None:
        self.store = store

    async def complete_scan(self, scan_id: UUID, ledger: CompletedScanLedger) -> None:
        validate_completed_ledger(ledger)
        await self.store.complete_scan(scan_id, ledger)


def validate_completed_ledger(ledger: CompletedScanLedger) -> None:
    if not _COMMIT_SHA.fullmatch(ledger.commit_sha):
        raise EvidenceContractError("commit_sha must be a 40-character lowercase Git SHA")
    if ledger.coverage_state not in {"complete", "partial"}:
        raise EvidenceContractError("coverage_state must be complete or partial")
    if ledger.coverage_state == "complete" and ledger.coverage_reasons:
        raise EvidenceContractError("complete coverage cannot contain reasons")
    if ledger.coverage_state == "partial" and not ledger.coverage_reasons:
        raise EvidenceContractError("partial coverage requires at least one reason")

    files_by_path = {}
    allowed_purposes = {item.value for item in FilePurpose}
    for file in ledger.files:
        if not file.path or file.path.startswith(("/", "\\")) or "\\" in file.path:
            raise EvidenceContractError("file paths must be repository-relative POSIX paths")
        if any(part == ".." for part in file.path.split("/")):
            raise EvidenceContractError("file paths cannot traverse parent directories")
        if file.path in files_by_path:
            raise EvidenceContractError(f"duplicate file path: {file.path}")
        if file.size_bytes < 0 or file.purpose not in allowed_purposes:
            raise EvidenceContractError(f"invalid inventory metadata for {file.path}")
        if file.inspected:
            valid_hash = bool(file.content_hash and _SHA256.fullmatch(file.content_hash))
            if file.skip_reason is not None or not valid_hash:
                raise EvidenceContractError(
                    f"inspected file requires one SHA-256 hash: {file.path}"
                )
        elif not file.skip_reason or file.content_hash is not None:
            raise EvidenceContractError(f"skipped file requires only a skip reason: {file.path}")
        files_by_path[file.path] = file

    allowed_confidence = {item.value for item in Confidence}
    semantic_keys: set[tuple[object, ...]] = set()
    for evidence in ledger.evidence:
        source_file = files_by_path.get(evidence.file_path)
        if source_file is None or not source_file.inspected:
            raise EvidenceContractError("evidence must reference an inspected file")
        if evidence.source_content_hash != source_file.content_hash:
            raise EvidenceContractError("evidence and file content hashes must match")
        if not evidence.canonical_skill_id or not evidence.rule_id:
            raise EvidenceContractError("evidence skill and rule identifiers are required")
        if evidence.evidence_kind not in EVIDENCE_KINDS:
            raise EvidenceContractError("evidence kind is outside contract 0.1")
        if evidence.confidence not in allowed_confidence:
            raise EvidenceContractError("evidence confidence is outside contract 0.1")
        if evidence.start_line < 1 or evidence.end_line < evidence.start_line:
            raise EvidenceContractError("evidence line range is invalid")
        if not evidence.redacted_excerpt:
            raise EvidenceContractError("redacted evidence excerpt cannot be empty")
        key = (
            evidence.file_path,
            evidence.canonical_skill_id,
            evidence.rule_id,
            evidence.start_line,
            evidence.end_line,
        )
        if key in semantic_keys:
            raise EvidenceContractError("duplicate semantic evidence")
        semantic_keys.add(key)
