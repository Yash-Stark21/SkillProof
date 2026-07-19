"""Safe parsing and normalization for public GitHub repository URLs."""

from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit

from app.domain.repository import NormalizedRepository

_OWNER_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")


class RepositoryUrlError(ValueError):
    """A submitted URL is not an accepted public GitHub repository URL."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def normalize_github_repository_url(value: str) -> NormalizedRepository:
    """Return a canonical GitHub identity without performing a network request."""

    candidate = value.strip()
    if not candidate:
        raise RepositoryUrlError("blank", "Enter a public GitHub repository URL.")

    try:
        parsed = urlsplit(candidate)
    except ValueError as exc:
        raise RepositoryUrlError(
            "invalid_url", "Enter a valid HTTPS GitHub repository URL."
        ) from exc

    if parsed.scheme.lower() != "https":
        raise RepositoryUrlError(
            "unsupported_scheme", "Only HTTPS GitHub repository URLs are supported."
        )
    if parsed.username is not None or parsed.password is not None:
        raise RepositoryUrlError(
            "embedded_credentials", "Repository URLs cannot contain credentials."
        )
    if parsed.hostname is None or parsed.hostname.lower() != "github.com":
        raise RepositoryUrlError(
            "unsupported_host", "Only public github.com repository URLs are supported."
        )
    try:
        port = parsed.port
    except ValueError as exc:
        raise RepositoryUrlError(
            "invalid_port", "Repository URLs cannot contain a custom port."
        ) from exc
    if port is not None:
        raise RepositoryUrlError("custom_port", "Repository URLs cannot contain a custom port.")
    if parsed.query or parsed.fragment:
        raise RepositoryUrlError(
            "query_or_fragment", "Repository URLs cannot contain a query or fragment."
        )

    decoded_path = unquote(parsed.path)
    segments = [segment for segment in decoded_path.split("/") if segment]
    if len(segments) != 2:
        raise RepositoryUrlError(
            "repository_path_required",
            "Use a repository URL in the form https://github.com/owner/repository.",
        )

    owner, repository = segments
    if repository.lower().endswith(".git"):
        repository = repository[:-4]
    if not _OWNER_PATTERN.fullmatch(owner):
        raise RepositoryUrlError("invalid_owner", "The GitHub repository owner is invalid.")
    if not _REPOSITORY_PATTERN.fullmatch(repository) or repository in {".", ".."}:
        raise RepositoryUrlError("invalid_repository", "The GitHub repository name is invalid.")

    return NormalizedRepository(
        provider="github",
        normalized_owner=owner.lower(),
        normalized_name=repository.lower(),
        display_owner=owner,
        display_name=repository,
        canonical_url=f"https://github.com/{owner}/{repository}",
    )
