import pytest

from zoo_mcp import ZooMCPException
from zoo_mcp.zoo_tools import _check_kcl_code_or_path


def test_check_kcl_code_or_path_with_code_only():
    """Test that providing only kcl_code works without error."""
    _check_kcl_code_or_path(kcl_code="some kcl code", kcl_path=None)


def test_check_kcl_code_or_path_with_kcl_file(cube_kcl: str):
    """Test that providing a valid .kcl file path works without error."""
    _check_kcl_code_or_path(kcl_code=None, kcl_path=cube_kcl)


def test_check_kcl_code_or_path_with_project_dir(kcl_project: str):
    """Test that providing a directory with main.kcl works without error."""
    _check_kcl_code_or_path(kcl_code=None, kcl_path=kcl_project)


def test_check_kcl_code_or_path_with_both(cube_kcl: str, caplog):
    """Test that providing both code and path uses code (logs warning)."""
    import logging

    caplog.set_level(logging.WARNING)
    # Should not raise, but should log a warning
    _check_kcl_code_or_path(kcl_code="some kcl code", kcl_path=cube_kcl)
    assert "Both code and kcl_path provided, using code" in caplog.text


def test_check_kcl_code_or_path_neither_provided():
    """Test that providing neither code nor path raises an exception."""
    with pytest.raises(ZooMCPException) as exc_info:
        _check_kcl_code_or_path(kcl_code=None, kcl_path=None)
    assert "Neither code nor kcl_path provided" in str(exc_info.value)


def test_check_kcl_code_or_path_empty_strings():
    """Test that providing empty strings for both raises an exception."""
    with pytest.raises(ZooMCPException) as exc_info:
        _check_kcl_code_or_path(kcl_code="", kcl_path="")
    assert "Neither code nor kcl_path provided" in str(exc_info.value)


def test_check_kcl_code_or_path_non_kcl_file(cube_stl: str):
    """Test that providing a non-.kcl file raises an exception."""
    with pytest.raises(ZooMCPException) as exc_info:
        _check_kcl_code_or_path(kcl_code=None, kcl_path=cube_stl)
    assert "not a .kcl file" in str(exc_info.value)


def test_check_kcl_code_or_path_dir_without_main_kcl(tmp_path):
    """Test that providing a directory without main.kcl raises an exception."""
    # Create an empty temp directory (no main.kcl)
    with pytest.raises(ZooMCPException) as exc_info:
        _check_kcl_code_or_path(kcl_code=None, kcl_path=str(tmp_path))
    assert "does not contain a main.kcl file" in str(exc_info.value)


def test_check_kcl_code_or_path_dir_without_main_kcl_not_required(tmp_path):
    """Test that providing a directory without main.kcl passes when require_main_file=False."""
    # Create a temp directory with a .kcl file but no main.kcl
    (tmp_path / "other.kcl").write_text("// some kcl code")
    # Should not raise when require_main_file=False
    _check_kcl_code_or_path(
        kcl_code=None, kcl_path=str(tmp_path), require_main_file=False
    )


def test_check_kcl_code_or_path_nonexistent_path():
    """Test that providing a nonexistent path raises an exception."""
    with pytest.raises(ZooMCPException) as exc_info:
        _check_kcl_code_or_path(kcl_code=None, kcl_path="/nonexistent/path/to/file.kcl")
    assert "does not exist" in str(exc_info.value)
