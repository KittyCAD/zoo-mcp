"""Shared utilities for fetching data from the modeling-app GitHub repository.

Provides common constants, path validation, content fetching, and text
extraction helpers used by both kcl_docs and kcl_samples modules.
"""

import posixpath
import re
from urllib.parse import unquote

import httpx

from zoo_mcp import logger

GITHUB_REPO = "KittyCAD/modeling-app"
_LATEST_RELEASE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def is_safe_path_component(value: str, pattern: re.Pattern[str]) -> bool:
    """Validate that a path component is safe"""
    if not value:
        return False

    # regex on raw value
    if not pattern.match(value):
        return False

    # decode and re-validate
    decoded = unquote(value)
    if not pattern.match(decoded):
        return False

    # normalize and verify no directory traversal
    normalized = posixpath.normpath(decoded)
    if normalized != decoded or normalized.startswith(".."):
        return False

    return True


async def resolve_latest_release_tag(client: httpx.AsyncClient) -> str | None:
    """Resolve the latest release tag from the GitHub API."""
    try:
        response = await client.get(_LATEST_RELEASE_URL)
        response.raise_for_status()
        tag = response.json().get("tag_name")
        if tag and isinstance(tag, str):
            return tag
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch latest release tag: {e}")
    return None


async def resolve_github_ref(client: httpx.AsyncClient) -> str:
    """Resolve the git ref to use for fetching content.

    Returns the latest release tag, or "main" as a fallback.
    """
    ref = await resolve_latest_release_tag(client)
    if ref:
        logger.info(f"Using release tag: {ref}")
        return ref

    logger.warning("Could not resolve latest release, falling back to main")
    return "main"


async def fetch_github_file(
    client: httpx.AsyncClient, url: str, label: str
) -> str | None:
    """Fetch a single file from GitHub raw content.

    Uses follow_redirects=False to prevent the server from silently
    resolving traversal paths to content outside the intended directory.

    Args:
        client: The HTTP client to use.
        url: The full URL to fetch.
        label: A human-readable label for log messages (e.g. the file path).

    Returns:
        The file content as a string, or None if the fetch failed.
    """
    try:
        response = await client.get(url, follow_redirects=False)
        if response.is_redirect:
            logger.warning(
                f"Rejected redirect for {label}: {response.headers.get('location')}"
            )
            return None
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch {label}: {e}")
        return None


def extract_excerpt(content: str, query: str, context_chars: int = 200) -> str:
    """Extract an excerpt around the first match of query in content."""
    query_lower = query.lower()
    content_lower = content.lower()

    pos = content_lower.find(query_lower)
    if pos == -1:
        # Return first context_chars of content as fallback
        return content[:context_chars].strip() + "..."

    # Find start and end positions for excerpt
    start = max(0, pos - context_chars // 2)
    end = min(len(content), pos + len(query) + context_chars // 2)

    # Adjust to word boundaries
    if start > 0:
        while start > 0 and content[start - 1] not in " \n\t":
            start -= 1

    if end < len(content):
        while end < len(content) and content[end] not in " \n\t":
            end += 1

    excerpt = content[start:end].strip()

    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(content) else ""

    return f"{prefix}{excerpt}{suffix}"
