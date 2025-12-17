"""Tests for KCL documentation fetching and search using live GitHub data."""

import json
from collections.abc import Sequence

import pytest
import pytest_asyncio
from mcp.types import TextContent

from zoo_mcp import kcl_docs
from zoo_mcp.kcl_docs import DocsCache
from zoo_mcp.server import mcp


@pytest_asyncio.fixture(scope="module")
async def live_docs_cache():
    """Initialize documentation cache from live GitHub data.

    This fixture fetches real documentation from GitHub once per test module,
    providing a more realistic test of the documentation system.
    """
    # Initialize the docs cache from GitHub
    await DocsCache.initialize()

    # Verify docs were fetched
    assert DocsCache._instance is not None, "Docs cache should be initialized"
    assert len(DocsCache._instance.docs) > 0, "Should have fetched some docs"

    yield DocsCache._instance

    # No cleanup needed - cache persists for module


@pytest.mark.asyncio
async def test_list_kcl_docs(live_docs_cache):
    """Test that list_kcl_docs returns categorized documentation."""
    response = await mcp.call_tool("list_kcl_docs", arguments={})
    assert isinstance(response, Sequence)
    assert len(response) > 0
    assert isinstance(response[0], TextContent)
    result = json.loads(response[0].text)

    assert isinstance(result, dict)
    # Check all expected categories exist
    assert "kcl-lang" in result
    assert "kcl-std-functions" in result
    assert "kcl-std-types" in result
    assert "kcl-std-consts" in result
    assert "kcl-std-modules" in result

    # Verify we have docs in each major category
    assert len(result["kcl-lang"]) > 0, "Should have KCL language docs"
    assert len(result["kcl-std-functions"]) > 0, "Should have std function docs"
    assert len(result["kcl-std-types"]) > 0, "Should have std type docs"


@pytest.mark.asyncio
async def test_search_kcl_docs(live_docs_cache):
    """Test that search_kcl_docs returns relevant excerpts for 'extrude'."""
    response = await mcp.call_tool(
        "search_kcl_docs", arguments={"query": "extrude", "max_results": 5}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    # FastMCP returns list results as [list_of_TextContent]
    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) > 0, "Should find results for 'extrude'"

    # Parse all results
    result = [json.loads(tc.text) for tc in inner_list]

    # Check result structure
    first_result = result[0]
    assert "path" in first_result
    assert "title" in first_result
    assert "excerpt" in first_result
    assert "match_count" in first_result

    # The extrude function doc should be in the results
    paths = [r["path"] for r in result]
    assert any(
        "extrude" in p.lower() for p in paths
    ), "Should find extrude-related docs"


@pytest.mark.asyncio
async def test_search_kcl_docs_sketch(live_docs_cache):
    """Test searching for 'sketch' returns relevant results."""
    response = await mcp.call_tool(
        "search_kcl_docs", arguments={"query": "sketch", "max_results": 10}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) > 0, "Should find results for 'sketch'"

    result = [json.loads(tc.text) for tc in inner_list]

    # Should find sketch-related docs
    all_text = " ".join([r["title"] + r["excerpt"] for r in result]).lower()
    assert "sketch" in all_text, "Results should contain 'sketch'"


@pytest.mark.asyncio
async def test_search_kcl_docs_no_results(live_docs_cache):
    """Test that search_kcl_docs handles queries with no matches."""
    response = await mcp.call_tool(
        "search_kcl_docs",
        arguments={"query": "xyznonexistentterm12345abc", "max_results": 5},
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) == 0, "Should find no results for gibberish query"


@pytest.mark.asyncio
async def test_search_kcl_docs_empty_query(live_docs_cache):
    """Test that search_kcl_docs handles empty queries."""
    response = await mcp.call_tool(
        "search_kcl_docs", arguments={"query": "", "max_results": 5}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) == 1

    result = json.loads(inner_list[0].text)
    assert "error" in result


@pytest.mark.asyncio
async def test_get_kcl_doc_functions(live_docs_cache):
    """Test that get_kcl_doc retrieves the functions documentation."""
    response = await mcp.call_tool(
        "get_kcl_doc", arguments={"doc_path": "docs/kcl-lang/functions.md"}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) == 1

    result = inner_list[0].text
    assert isinstance(result, str)
    # Should contain content about functions
    assert "function" in result.lower(), "Should mention functions"
    assert len(result) > 100, "Should have substantial content"


@pytest.mark.asyncio
async def test_get_kcl_doc_extrude(live_docs_cache):
    """Test that get_kcl_doc retrieves the extrude function documentation."""
    response = await mcp.call_tool(
        "get_kcl_doc", arguments={"doc_path": "docs/kcl-std/functions/extrude.md"}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) == 1

    result = inner_list[0].text
    assert isinstance(result, str)
    assert "extrude" in result.lower(), "Should mention extrude"


@pytest.mark.asyncio
async def test_get_kcl_doc_not_found(live_docs_cache):
    """Test that get_kcl_doc handles missing documentation."""
    response = await mcp.call_tool(
        "get_kcl_doc", arguments={"doc_path": "docs/nonexistent/fake.md"}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) == 1

    result = inner_list[0].text
    assert isinstance(result, str)
    assert "Documentation not found" in result


@pytest.mark.asyncio
async def test_get_kcl_doc_path_traversal(live_docs_cache):
    """Test that get_kcl_doc rejects path traversal attempts."""
    response = await mcp.call_tool(
        "get_kcl_doc", arguments={"doc_path": "../../../etc/passwd"}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) == 1

    result = inner_list[0].text
    assert isinstance(result, str)
    assert "Documentation not found" in result


def test_extract_title():
    """Test title extraction from Markdown content."""
    content = "# My Title\n\nSome content here."
    assert kcl_docs._extract_title(content) == "My Title"

    # Test with no title
    content_no_title = "Some content without a heading."
    assert kcl_docs._extract_title(content_no_title) == ""


def test_extract_excerpt():
    """Test excerpt extraction with context."""
    content = "This is some text before. The keyword appears here in the middle. And this is text after."
    excerpt = kcl_docs._extract_excerpt(content, "keyword", context_chars=40)

    assert "keyword" in excerpt
    assert len(excerpt) < len(content) + 10  # Account for ellipsis


def test_categorize_doc_path():
    """Test documentation path categorization."""
    assert kcl_docs._categorize_doc_path("docs/kcl-lang/functions.md") == "kcl-lang"
    assert (
        kcl_docs._categorize_doc_path("docs/kcl-std/functions/extrude.md")
        == "kcl-std-functions"
    )
    assert (
        kcl_docs._categorize_doc_path("docs/kcl-std/types/Sketch.md") == "kcl-std-types"
    )
    assert (
        kcl_docs._categorize_doc_path("docs/kcl-std/consts/PI.md") == "kcl-std-consts"
    )
    assert (
        kcl_docs._categorize_doc_path("docs/kcl-std/modules/math.md")
        == "kcl-std-modules"
    )
    assert kcl_docs._categorize_doc_path("docs/other/file.md") is None
