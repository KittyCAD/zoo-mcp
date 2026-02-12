"""KCL Documentation fetching and search.

This module fetches KCL documentation from the modeling-app GitHub repository
at server startup and provides search functionality for LLMs.
"""

import asyncio
import re
from dataclasses import dataclass, field
from posixpath import normpath
from typing import ClassVar
from urllib.parse import unquote

import httpx

from zoo_mcp import logger
from zoo_mcp.utils.data_retrieval_utils import (
    GITHUB_REPO,
    extract_excerpt,
    fetch_github_file,
    is_safe_path_component,
    resolve_github_ref,
)

# Only allow safe characters in doc paths
_SAFE_DOC_PATH_RE = re.compile(r"^docs/[A-Za-z0-9/_-]+\.md$")


def _is_safe_doc_path(path: str) -> bool:
    """Validate that a doc path is safe and does not contain traversal sequences."""
    if not is_safe_path_component(path, _SAFE_DOC_PATH_RE):
        return False

    # Additional check: after normalization the path must still be under docs/
    normalized = normpath(unquote(path))
    if not normalized.startswith("docs/"):
        return False

    return True


@dataclass
class KCLDocs:
    """Container for documentation data."""

    docs: dict[str, str] = field(default_factory=dict)
    index: dict[str, list[str]] = field(
        default_factory=lambda: {
            "kcl-lang": [],
            "kcl-std-functions": [],
            "kcl-std-types": [],
            "kcl-std-consts": [],
            "kcl-std-modules": [],
        }
    )

    _instance: ClassVar["KCLDocs | None"] = None

    @classmethod
    def get(cls) -> "KCLDocs":
        """Get the cached docs instance, or empty cache if not initialized."""
        return cls._instance if cls._instance is not None else cls()

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the docs cache from GitHub."""
        if cls._instance is None:
            cls._instance = await _fetch_docs_from_github()


def _categorize_doc_path(path: str) -> str | None:
    """Categorize a doc path into one of the index categories."""
    if path.startswith("docs/kcl-lang/"):
        return "kcl-lang"
    elif path.startswith("docs/kcl-std/functions/"):
        return "kcl-std-functions"
    elif path.startswith("docs/kcl-std/types/"):
        return "kcl-std-types"
    elif path.startswith("docs/kcl-std/consts/"):
        return "kcl-std-consts"
    elif path.startswith("docs/kcl-std/modules/"):
        return "kcl-std-modules"
    elif path.startswith("docs/kcl-std/"):
        # Other kcl-std files (index.md, README.md)
        return None
    return None


def _extract_title(content: str) -> str:
    """Extract the title from Markdown content (first # heading)."""
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


async def _fetch_docs_from_github() -> KCLDocs:
    """Fetch all docs from GitHub and return a KCLDocs.

    Uses the latest tagged release instead of the main branch.
    """
    docs = KCLDocs()

    logger.info("Fetching KCL documentation from GitHub...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Resolve the latest release tag (fall back to "main" if unavailable)
        ref = await resolve_github_ref(client)

        tree_url = (
            f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/{ref}?recursive=1"
        )
        raw_content_base = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{ref}/"

        # 2. Get file tree from GitHub API
        try:
            response = await client.get(tree_url)
            response.raise_for_status()
            tree_data = response.json()
        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch GitHub tree: {e}")
            return docs

        # 3. Filter for docs/*.md files
        doc_paths: list[str] = []
        for item in tree_data.get("tree", []):
            path = item.get("path", "")
            if item.get("type") == "blob" and _is_safe_doc_path(path):
                doc_paths.append(path)

        logger.info(f"Found {len(doc_paths)} documentation files")

        # 4. Fetch raw content in parallel
        tasks = [
            fetch_github_file(client, f"{raw_content_base}{path}", path)
            for path in doc_paths
        ]
        results = await asyncio.gather(*tasks)

        # 5. Populate cache and index
        for path, content in zip(doc_paths, results):
            if content is not None:
                docs.docs[path] = content

                # Categorize the doc
                category = _categorize_doc_path(path)
                if category and category in docs.index:
                    docs.index[category].append(path)

    # Sort the index lists
    for category in docs.index:
        docs.index[category].sort()

    logger.info(f"KCL documentation cache initialized with {len(docs.docs)} files")
    return docs


async def initialize_docs_cache() -> None:
    """Initialize the docs cache from GitHub."""
    await KCLDocs.initialize()


def list_available_docs() -> dict[str, list[str]]:
    """Return categorized list of available documentation.

    Returns a dictionary with the following categories:
    - kcl-lang: KCL language documentation (syntax, types, functions, etc.)
    - kcl-std-functions: Standard library function documentation
    - kcl-std-types: Standard library type documentation
    - kcl-std-consts: Standard library constants documentation
    - kcl-std-modules: Standard library module documentation

    Each category contains a list of documentation file paths that can be
    retrieved using get_kcl_doc().

    Returns:
        dict: Categories mapped to lists of available documentation paths.
    """
    return KCLDocs.get().index


def search_docs(query: str, max_results: int = 5) -> list[dict]:
    """Search docs by keyword.

    Searches across all KCL language and standard library documentation
    for the given query. Returns relevant excerpts with surrounding context.

    Args:
        query (str): The search query (case-insensitive).
        max_results (int): Maximum number of results to return (default: 5).

    Returns:
        list[dict]: List of search results, each containing:
            - path: The documentation file path
            - title: The document title (from first heading)
            - excerpt: A relevant excerpt with the match highlighted in context
            - match_count: Number of times the query appears in the document
    """

    if not query or not query.strip():
        return [{"error": "Empty search query"}]

    query = query.strip()
    query_lower = query.lower()
    results: list[dict] = []

    for path, content in KCLDocs.get().docs.items():
        content_lower = content.lower()

        # Count matches
        match_count = content_lower.count(query_lower)
        if match_count > 0:
            title = _extract_title(content)
            excerpt = extract_excerpt(content, query)

            results.append(
                {
                    "path": path,
                    "title": title,
                    "excerpt": excerpt,
                    "match_count": match_count,
                }
            )

    # Sort by match count (descending)
    results.sort(key=lambda x: x["match_count"], reverse=True)

    return results[:max_results]


def get_doc_content(doc_path: str) -> str | None:
    """Get the full content of a specific KCL documentation file.

    Use list_kcl_docs() to see available documentation paths, or
    search_kcl_docs() to find relevant documentation by keyword.

    Args:
        doc_path (str): The path to the documentation file
            (e.g., "docs/kcl-lang/functions.md" or "docs/kcl-std/functions/extrude.md")

    Returns:
        str: The full Markdown content of the documentation file,
            or an error message if not found.
    """

    if not _is_safe_doc_path(doc_path):
        return None

    return KCLDocs.get().docs.get(doc_path)
