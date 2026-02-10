"""KCL Samples fetching and search.

This module fetches KCL samples from the modeling-app GitHub repository
at server startup and provides search functionality for LLMs.
"""

import asyncio
import re
from dataclasses import dataclass, field
from typing import ClassVar, TypedDict

import httpx

from zoo_mcp import logger
from zoo_mcp.utils.data_retrieval_utils import (
    GITHUB_REPO,
    extract_excerpt,
    fetch_github_file,
    is_safe_path_component,
    resolve_github_ref,
)

_SAMPLES_PATH = "public/kcl-samples"

# Only allow safe characters in sample names and filenames
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_-]+\.kcl$")


class SampleMetadata(TypedDict):
    """Metadata for a single KCL sample from manifest.json."""

    file: str
    pathFromProjectDirectoryToFirstFile: str
    multipleFiles: bool
    title: str
    description: str
    files: list[str]


class SampleFile(TypedDict):
    """A single file within a KCL sample."""

    filename: str
    content: str


class SampleData(TypedDict):
    """Complete data for a KCL sample including all files."""

    name: str
    title: str
    description: str
    multipleFiles: bool
    files: list[SampleFile]


@dataclass
class KCLSamples:
    """Container for KCL samples data."""

    # Manifest data indexed by sample directory name
    manifest: dict[str, SampleMetadata] = field(default_factory=dict)
    # Cached file contents: sample_name -> filename -> content
    file_cache: dict[str, dict[str, str]] = field(default_factory=dict)
    # Git ref (release tag) used to fetch content
    _ref: str = "main"

    _instance: ClassVar["KCLSamples | None"] = None

    @classmethod
    def get(cls) -> "KCLSamples":
        """Get the cached samples instance, or empty cache if not initialized."""
        return cls._instance if cls._instance is not None else cls()

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the samples cache from GitHub."""
        if cls._instance is None:
            cls._instance = await _fetch_manifest_from_github()


def _extract_sample_name(path: str) -> str:
    """Extract the sample directory name from a path.

    Example: "axial-fan/main.kcl" -> "axial-fan"
    """
    return path.split("/")[0] if "/" in path else path


async def _fetch_sample_files(
    client: httpx.AsyncClient,
    raw_content_base: str,
    sample_name: str,
    filenames: list[str],
) -> dict[str, str]:
    """Fetch all files for a sample."""
    tasks = [
        fetch_github_file(
            client,
            f"{raw_content_base}{sample_name}/{filename}",
            f"{sample_name}/{filename}",
        )
        for filename in filenames
    ]
    results = await asyncio.gather(*tasks)
    return {
        filename: content
        for filename, content in zip(filenames, results)
        if content is not None
    }


async def _fetch_manifest_from_github() -> KCLSamples:
    """Fetch the manifest from GitHub and return a KCLSamples instance."""
    samples = KCLSamples()

    logger.info("Fetching KCL samples manifest from GitHub...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Resolve the latest release tag (fall back to "main" if unavailable)
        ref = await resolve_github_ref(client)

        raw_content_base = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{ref}/{_SAMPLES_PATH}/"
        manifest_url = f"{raw_content_base}manifest.json"

        # Store ref for later use when fetching sample files on-demand
        samples._ref = ref

        try:
            response = await client.get(manifest_url)
            response.raise_for_status()
            manifest_data: list[SampleMetadata] = response.json()
        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch samples manifest: {e}")
            return samples

        # Index manifest by sample name, validating each name
        for entry in manifest_data:
            sample_name = _extract_sample_name(
                entry.get("pathFromProjectDirectoryToFirstFile", "")
            )
            if sample_name and is_safe_path_component(sample_name, _SAFE_NAME_RE):
                samples.manifest[sample_name] = entry
            elif sample_name:
                logger.warning(f"Rejected unsafe sample name from manifest: {sample_name!r}")

    logger.info(f"KCL samples manifest loaded with {len(samples.manifest)} samples")
    return samples


async def initialize_samples_cache() -> None:
    """Initialize the samples cache from GitHub."""
    await KCLSamples.initialize()


def list_available_samples() -> list[dict]:
    """Return a list of all available KCL samples with basic info.

    Returns a list of dictionaries, each containing:
    - name: The sample directory name (used to retrieve the sample)
    - title: Human-readable title
    - description: Brief description of the sample
    - multipleFiles: Whether the sample contains multiple KCL files

    Use get_kcl_sample() with the name to retrieve the full sample content.

    Returns:
        list[dict]: List of sample information dictionaries.
    """
    samples = KCLSamples.get()
    result = []

    for name, metadata in sorted(samples.manifest.items()):
        result.append(
            {
                "name": name,
                "title": metadata.get("title", name),
                "description": metadata.get("description", ""),
                "multipleFiles": metadata.get("multipleFiles", False),
            }
        )

    return result


def search_samples(query: str, max_results: int = 5) -> list[dict]:
    """Search samples by keyword in title and description.

    Searches across all KCL sample titles and descriptions
    for the given query. Returns matching samples ranked by relevance.

    Args:
        query (str): The search query (case-insensitive).
        max_results (int): Maximum number of results to return (default: 5).

    Returns:
        list[dict]: List of search results, each containing:
            - name: The sample directory name (used to retrieve the sample)
            - title: Human-readable title
            - description: Brief description of the sample
            - multipleFiles: Whether the sample contains multiple KCL files
            - match_count: Number of times the query appears in title/description
            - excerpt: A relevant excerpt with the match in context
    """
    if not query or not query.strip():
        return [{"error": "Empty search query"}]

    query = query.strip()
    query_lower = query.lower()
    results: list[dict] = []

    samples = KCLSamples.get()

    for name, metadata in samples.manifest.items():
        title = metadata.get("title", name)
        description = metadata.get("description", "")
        searchable = f"{title} {description} {name}"
        searchable_lower = searchable.lower()

        match_count = searchable_lower.count(query_lower)
        if match_count > 0:
            # Prioritize title matches
            title_matches = title.lower().count(query_lower)
            score = match_count + (title_matches * 3)  # Boost title matches

            excerpt = extract_excerpt(searchable, query, context_chars=150)

            results.append(
                {
                    "name": name,
                    "title": title,
                    "description": description,
                    "multipleFiles": metadata.get("multipleFiles", False),
                    "match_count": match_count,
                    "excerpt": excerpt,
                    "_score": score,
                }
            )

    # Sort by score (descending)
    results.sort(key=lambda x: x["_score"], reverse=True)

    # Remove internal score field
    for r in results:
        del r["_score"]

    return results[:max_results]


async def get_sample_content(sample_name: str) -> SampleData | None:
    """Get the full content of a specific KCL sample including all files.

    Use list_kcl_samples() to see available sample names, or
    search_kcl_samples() to find samples by keyword.

    Args:
        sample_name (str): The sample directory name
            (e.g., "ball-bearing", "axial-fan")

    Returns:
        SampleData | None: A dictionary containing:
            - name: The sample directory name
            - title: Human-readable title
            - description: Brief description
            - multipleFiles: Whether the sample contains multiple files
            - files: List of file dictionaries, each with 'filename' and 'content'
        Returns None if the sample is not found.
    """
    samples = KCLSamples.get()

    # Validate sample name against allowlist
    if not is_safe_path_component(sample_name, _SAFE_NAME_RE):
        return None

    metadata = samples.manifest.get(sample_name)
    if metadata is None:
        return None

    # Check if we have cached files
    if sample_name in samples.file_cache:
        file_contents = samples.file_cache[sample_name]
    else:
        # Validate and filter filenames from manifest
        raw_filenames = metadata.get("files", ["main.kcl"])
        filenames = []
        for f in raw_filenames:
            if is_safe_path_component(f, _SAFE_FILENAME_RE):
                filenames.append(f)
            else:
                logger.warning(f"Rejected unsafe filename in sample {sample_name!r}: {f!r}")

        if not filenames:
            return None

        raw_content_base = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{samples._ref}/{_SAMPLES_PATH}/"

        async with httpx.AsyncClient(timeout=30.0) as client:
            file_contents = await _fetch_sample_files(
                client, raw_content_base, sample_name, filenames
            )

        # Cache the results
        samples.file_cache[sample_name] = file_contents

    # Build response
    files_list: list[SampleFile] = []
    for filename, content in sorted(file_contents.items()):
        files_list.append(SampleFile(filename=filename, content=content))

    return SampleData(
        name=sample_name,
        title=metadata.get("title", sample_name),
        description=metadata.get("description", ""),
        multipleFiles=metadata.get("multipleFiles", False),
        files=files_list,
    )
