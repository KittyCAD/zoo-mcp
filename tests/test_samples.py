from zoo_mcp import kcl_samples
from zoo_mcp.utils.data_retrieval_utils import extract_excerpt


def test_extract_sample_name():
    """Test sample name extraction from path."""
    assert kcl_samples._extract_sample_name("axial-fan/main.kcl") == "axial-fan"
    assert kcl_samples._extract_sample_name("ball-bearing/main.kcl") == "ball-bearing"
    assert kcl_samples._extract_sample_name("gear") == "gear"


def test_extract_excerpt():
    """Test excerpt extraction with context."""
    content = "This is some text before. The keyword appears here in the middle. And this is text after."
    excerpt = extract_excerpt(content, "keyword", context_chars=40)

    assert "keyword" in excerpt
    assert len(excerpt) < len(content) + 10  # Account for ellipsis


def test_extract_excerpt_no_match():
    """Test excerpt extraction when query is not found."""
    content = "Some content without the search term."
    excerpt = extract_excerpt(content, "nonexistent", context_chars=50)

    # Should return beginning of content as fallback
    assert excerpt.startswith("Some content")


def test_list_available_samples_returns_list():
    """Test that list_available_samples returns a list."""
    # Without initialization, should return empty list
    result = kcl_samples.list_available_samples()
    assert isinstance(result, list)


def test_search_samples_empty_query():
    """Test search with empty query returns error."""
    result = kcl_samples.search_samples("")
    assert len(result) == 1
    assert "error" in result[0]

    result = kcl_samples.search_samples("   ")
    assert len(result) == 1
    assert "error" in result[0]


def test_search_samples_returns_list():
    """Test that search_samples returns a list."""
    result = kcl_samples.search_samples("gear")
    assert isinstance(result, list)
