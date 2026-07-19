"""Unit tests for strict, side-effect-free GitHub URL normalization."""

from __future__ import annotations

import pytest

from app.services.repository_url import (
    RepositoryUrlError,
    normalize_github_repository_url,
)


@pytest.mark.parametrize(
    ("submitted", "canonical"),
    [
        (
            "https://github.com/OpenAI/SkillProof",
            "https://github.com/OpenAI/SkillProof",
        ),
        (
            " https://github.com/OpenAI/SkillProof/ ",
            "https://github.com/OpenAI/SkillProof",
        ),
        (
            "https://github.com/OpenAI/SkillProof.git",
            "https://github.com/OpenAI/SkillProof",
        ),
    ],
)
def test_normalizes_supported_github_repository_urls(submitted: str, canonical: str) -> None:
    repository = normalize_github_repository_url(submitted)

    assert repository.provider == "github"
    assert repository.normalized_owner == "openai"
    assert repository.normalized_name == "skillproof"
    assert repository.display_owner == "OpenAI"
    assert repository.display_name == "SkillProof"
    assert repository.canonical_url == canonical
    assert repository.identity == "github:openai/skillproof"
    assert repository.api_snapshot() == {
        "provider": "github",
        "identity": "github:openai/skillproof",
        "owner": "OpenAI",
        "name": "SkillProof",
        "url": canonical,
    }


@pytest.mark.parametrize(
    ("submitted", "expected_code"),
    [
        ("", "blank"),
        ("http://github.com/openai/skillproof", "unsupported_scheme"),
        ("git@github.com:openai/skillproof.git", "unsupported_scheme"),
        ("https://gitlab.com/openai/skillproof", "unsupported_host"),
        ("https://user:secret@github.com/openai/skillproof", "embedded_credentials"),
        ("https://github.com:8443/openai/skillproof", "custom_port"),
        ("https://github.com/openai/skillproof?tab=readme", "query_or_fragment"),
        ("https://github.com/openai/skillproof#readme", "query_or_fragment"),
        ("https://github.com/openai", "repository_path_required"),
        ("https://github.com/openai/skillproof/tree/main", "repository_path_required"),
        ("https://github.com/openai/..", "invalid_repository"),
    ],
)
def test_rejects_noncanonical_or_unsafe_repository_urls(submitted: str, expected_code: str) -> None:
    with pytest.raises(RepositoryUrlError) as caught:
        normalize_github_repository_url(submitted)

    assert caught.value.code == expected_code
    assert caught.value.message


def test_percent_decoding_cannot_hide_a_repository_subpath() -> None:
    with pytest.raises(RepositoryUrlError) as caught:
        normalize_github_repository_url("https://github.com/openai/skillproof%2Ftree%2Fmain")

    assert caught.value.code == "repository_path_required"
