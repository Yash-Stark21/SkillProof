"""Frozen version identifiers and bounded scan-policy defaults."""

DETECTOR_VERSION = "0.1.0"
TAXONOMY_VERSION = "0.1.0"
REDACTION_VERSION = "0.1.0"
EVIDENCE_CONTRACT_VERSION = "0.1"
SCAN_POLICY_VERSION = "0.1"

SCAN_POLICY_LIMITS: dict[str, int] = {
    "github_requests": 50,
    "tree_entries": 10_000,
    "file_blobs": 40,
    "per_file_bytes": 262_144,
    "total_file_bytes": 5_242_880,
    "concurrency": 5,
    "request_timeout_seconds": 10,
}

EMPTY_SCAN_OBSERVATIONS: dict[str, int] = {
    "github_requests": 0,
    "tree_entries": 0,
    "file_blobs": 0,
    "largest_file_bytes": 0,
    "total_file_bytes": 0,
    "maximum_concurrency": 0,
}
