from collections.abc import Sequence
from pathlib import Path

import pytest
from mcp.types import ImageContent

from zoo_mcp import ZooMCPException
from zoo_mcp.server import mcp
from zoo_mcp.zoo_tools import _check_kcl_code_or_path


@pytest.fixture
def cube_kcl():
    test_file = Path(__file__).parent / "data" / "cube.kcl"
    yield f"{test_file.resolve()}"


@pytest.fixture
def cube_stl():
    test_file = Path(__file__).parent / "data" / "cube.stl"
    yield f"{test_file.resolve()}"


@pytest.fixture
def empty_kcl():
    test_file = Path(__file__).parent / "data" / "empty.kcl"
    yield f"{test_file.resolve()}"


@pytest.fixture
def empty_step():
    test_file = Path(__file__).parent / "data" / "empty.step"
    yield f"{test_file.resolve()}"


@pytest.fixture
def kcl_project():
    project_path = Path(__file__).parent / "data" / "test_kcl_project"
    yield f"{project_path.resolve()}"


@pytest.fixture
def box_with_linter_errors():
    test_file = Path(__file__).parent / "data" / "box_with_linter_errors.kcl"
    yield f"{test_file.resolve()}"


@pytest.mark.asyncio
async def test_calculate_center_of_mass(cube_stl: str):
    response = await mcp.call_tool(
        "calculate_center_of_mass",
        arguments={
            "input_file": cube_stl,
            "unit_length": "mm",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, dict)
    assert "x" in result and "y" in result and "z" in result
    assert result["x"] == pytest.approx(5.0)
    assert result["y"] == pytest.approx(5.0)
    assert result["z"] == pytest.approx(-5.0)


@pytest.mark.asyncio
async def test_calculate_center_of_mass_error(cube_stl: str):
    response = await mcp.call_tool(
        "calculate_center_of_mass",
        arguments={
            "input_file": cube_stl,
            "unit_length": "asdf",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "not a valid UnitLength" in result


@pytest.mark.asyncio
async def test_calculate_mass(cube_stl: str):
    response = await mcp.call_tool(
        "calculate_mass",
        arguments={
            "input_file": cube_stl,
            "unit_mass": "g",
            "unit_density": "kg:m3",
            "density": 1000.0,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, float)
    assert result == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_calculate_mass_error(cube_stl: str):
    response = await mcp.call_tool(
        "calculate_mass",
        arguments={
            "input_file": cube_stl,
            "unit_mass": "asdf",
            "unit_density": "kg:m3",
            "density": 1000.0,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "not a valid UnitMass" in result


@pytest.mark.asyncio
async def test_calculate_surface_area(cube_stl: str):
    response = await mcp.call_tool(
        "calculate_surface_area", arguments={"input_file": cube_stl, "unit_area": "mm2"}
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, float)
    assert result == pytest.approx(600.0)


@pytest.mark.asyncio
async def test_calculate_surface_area_error(cube_stl: str):
    response = await mcp.call_tool(
        "calculate_surface_area",
        arguments={
            "input_file": cube_stl,
            "unit_area": "asdf",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "not a valid UnitArea" in result


@pytest.mark.asyncio
async def test_calculate_volume(cube_stl: str):
    response = await mcp.call_tool(
        "calculate_volume", arguments={"input_file": cube_stl, "unit_volume": "cm3"}
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, float)
    assert result == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_calculate_volume_error(cube_stl: str):
    response = await mcp.call_tool(
        "calculate_volume", arguments={"input_file": cube_stl, "unit_volume": "asdf"}
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "not a valid UnitVolume" in result


@pytest.mark.asyncio
async def test_convert_cad_file(cube_stl: str):
    response = await mcp.call_tool(
        "convert_cad_file",
        arguments={
            "input_path": cube_stl,
            "export_path": None,
            "export_format": "obj",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert Path(result).exists()
    assert Path(result).stat().st_size != 0


@pytest.mark.asyncio
async def test_convert_cad_file_error(empty_step: str):
    response = await mcp.call_tool(
        "convert_cad_file",
        arguments={
            "input_path": empty_step,
            "export_path": None,
            "export_format": "asdf",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "error converting the CAD" in result


@pytest.mark.asyncio
async def test_execute_kcl(cube_kcl: str):
    response = await mcp.call_tool(
        "execute_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": cube_kcl,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, (tuple, list))
    assert result[0] is True
    assert "KCL code executed successfully" in result[1]


@pytest.mark.asyncio
async def test_execute_kcl_error():
    response = await mcp.call_tool(
        "execute_kcl",
        arguments={
            "kcl_code": "asdf = asdf",
            "kcl_path": None,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, (tuple, list))
    assert result[0] is False
    assert "Failed to execute KCL code" in result[1]


@pytest.mark.asyncio
async def test_export_kcl(cube_kcl: str):
    response = await mcp.call_tool(
        "export_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": cube_kcl,
            "export_path": None,
            "export_format": "step",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert Path(result).exists()
    assert Path(result).stat().st_size != 0


@pytest.mark.asyncio
async def test_export_kcl_error():
    response = await mcp.call_tool(
        "export_kcl",
        arguments={
            "kcl_code": "asdf",
            "kcl_path": None,
            "export_path": None,
            "export_format": "step",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "error exporting the CAD" in result


@pytest.mark.asyncio
async def test_format_kcl_path_success(cube_kcl: str):
    response = await mcp.call_tool(
        "format_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": cube_kcl,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "Successfully formatted KCL code at" in result


@pytest.mark.asyncio
async def test_format_kcl_str_success(cube_kcl: str):
    response = await mcp.call_tool(
        "format_kcl",
        arguments={
            "kcl_code": Path(cube_kcl).read_text(),
            "kcl_path": None,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "|>" in result


@pytest.mark.asyncio
async def test_format_kcl_error(cube_stl: str):
    response = await mcp.call_tool(
        "format_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": cube_stl,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "error formatting the KCL" in result


@pytest.mark.asyncio
async def test_lint_and_fix_kcl_str_success():
    code = """c = startSketchOn(XY)
  |> circle(center = [0, 0], radius = 1)
  |> circle(center = [5, 0], radius = 1)
  |> circle(center = [0,  5], radius = 1)
  |> circle(center = [5, 5], radius = 1)
"""
    response = await mcp.call_tool(
        "lint_and_fix_kcl",
        arguments={
            "kcl_code": code,
            "kcl_path": None,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    fixed_code, _ = response[1]["result"]
    assert fixed_code != code


@pytest.mark.asyncio
async def test_lint_and_fix_kcl_path_success(kcl_project: str):
    response = await mcp.call_tool(
        "lint_and_fix_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": kcl_project,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    fixed_code_msg, _ = response[1]["result"]
    assert "Successfully linted and fixed KCL code" in fixed_code_msg


@pytest.mark.asyncio
async def test_lint_and_fix_kcl_error(cube_stl: str):
    response = await mcp.call_tool(
        "lint_and_fix_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": cube_stl,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    fixed_code_msg, _ = response[1]["result"]
    assert "error linting and fixing" in fixed_code_msg


@pytest.mark.asyncio
async def test_mock_execute_kcl(cube_kcl: str):
    response = await mcp.call_tool(
        "mock_execute_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": cube_kcl,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, (tuple, list))
    assert result[0] is True
    assert "KCL code mock executed successfully" in result[1]


@pytest.mark.asyncio
async def test_mock_execute_kcl_error():
    response = await mcp.call_tool(
        "mock_execute_kcl",
        arguments={
            "kcl_code": "asdf = asdf",
            "kcl_path": None,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, (tuple, list))
    assert result[0] is False
    assert "Failed to mock execute KCL code" in result[1]


@pytest.mark.asyncio
async def test_multiview_snapshot_of_cad(cube_stl: str):
    response = await mcp.call_tool(
        "multiview_snapshot_of_cad",
        arguments={
            "input_file": cube_stl,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[0], list)
    result = response[0][0]
    assert isinstance(result, ImageContent)


@pytest.mark.asyncio
async def test_multiview_snapshot_of_cad_error(empty_step: str):
    response = await mcp.call_tool(
        "multiview_snapshot_of_cad",
        arguments={
            "input_file": empty_step,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "error creating the multiview snapshot" in result


@pytest.mark.asyncio
async def test_multiview_snapshot_of_kcl(cube_kcl: str):
    response = await mcp.call_tool(
        "multiview_snapshot_of_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": cube_kcl,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[0], list)
    result = response[0][0]
    assert isinstance(result, ImageContent)


@pytest.mark.asyncio
async def test_multiview_snapshot_of_kcl_error(empty_step: str):
    response = await mcp.call_tool(
        "multiview_snapshot_of_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": empty_step,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "error creating the multiview snapshot" in result


@pytest.mark.asyncio
async def test_snapshot_of_cad(cube_stl: str):
    response = await mcp.call_tool(
        "snapshot_of_cad",
        arguments={
            "input_file": cube_stl,
            "camera_view": "isometric",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[0], list)
    result = response[0][0]
    assert isinstance(result, ImageContent)


@pytest.mark.asyncio
async def test_snapshot_of_cad_error(empty_step: str):
    response = await mcp.call_tool(
        "snapshot_of_cad",
        arguments={
            "input_file": empty_step,
            "camera_view": "isometric",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "error creating the snapshot" in result


@pytest.mark.asyncio
async def test_snapshot_of_cad_camera(cube_stl: str):
    response = await mcp.call_tool(
        "snapshot_of_cad",
        arguments={
            "input_file": cube_stl,
            "camera_view": {
                "up": [0, 0, 1],
                "vantage": [0, -1, 0],
                "center": [0, 0, 0],
            },
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[0], list)
    result = response[0][0]
    assert isinstance(result, ImageContent)


@pytest.mark.asyncio
async def test_snapshot_of_cad_camera_error(empty_step: str):
    response = await mcp.call_tool(
        "snapshot_of_cad",
        arguments={
            "input_file": empty_step,
            "camera_view": {
                "hello": [0, 0, 0],
            },
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "error creating the snapshot" in result


@pytest.mark.asyncio
async def test_snapshot_of_cad_view(cube_stl: str):
    response = await mcp.call_tool(
        "snapshot_of_cad",
        arguments={
            "input_file": cube_stl,
            "camera_view": "front",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[0], list)
    result = response[0][0]
    assert isinstance(result, ImageContent)


@pytest.mark.asyncio
async def test_snapshot_of_cad_view_error(cube_stl: str):
    response = await mcp.call_tool(
        "snapshot_of_cad",
        arguments={
            "input_file": cube_stl,
            "camera_view": "asdf",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "Invalid camera view" in result


@pytest.mark.asyncio
async def test_snapshot_of_kcl(cube_kcl: str):
    response = await mcp.call_tool(
        "snapshot_of_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": cube_kcl,
            "camera_view": "isometric",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[0], list)
    result = response[0][0]
    assert isinstance(result, ImageContent)


@pytest.mark.asyncio
async def test_snapshot_of_kcl_error(empty_step: str):
    response = await mcp.call_tool(
        "snapshot_of_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": empty_step,
            "camera_view": "isometric",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "error creating the snapshot" in result


@pytest.mark.asyncio
async def test_snapshot_of_kcl_camera(cube_kcl: str):
    response = await mcp.call_tool(
        "snapshot_of_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": cube_kcl,
            "camera_view": {
                "up": [0, 0, 1],
                "vantage": [0, -1, 0],
                "center": [0, 0, 0],
            },
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[0], list)
    result = response[0][0]
    assert isinstance(result, ImageContent)


@pytest.mark.asyncio
async def test_snapshot_of_kcl_camera_error(empty_kcl: str):
    response = await mcp.call_tool(
        "snapshot_of_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": empty_kcl,
            "camera_view": {
                "hello": [0, 0, 0],
            },
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "error creating the snapshot" in result


@pytest.mark.asyncio
async def test_snapshot_of_kcl_view(cube_kcl: str):
    response = await mcp.call_tool(
        "snapshot_of_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": cube_kcl,
            "camera_view": "front",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[0], list)
    result = response[0][0]
    assert isinstance(result, ImageContent)


@pytest.mark.asyncio
async def test_snapshot_of_kcl_view_error(cube_kcl: str):
    response = await mcp.call_tool(
        "snapshot_of_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": cube_kcl,
            "camera_view": "asdf",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "Invalid camera view" in result


@pytest.mark.asyncio
async def test_text_to_cad_failure():
    prompt = "the quick brown fox jumps over the lazy dog"
    response = await mcp.call_tool("text_to_cad", arguments={"prompt": prompt})
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "400 Bad Request" in result


@pytest.mark.asyncio
@pytest.mark.flaky(reruns=3, reruns_delay=1)
async def test_text_to_cad_success(caplog):
    import logging

    caplog.set_level(logging.INFO)
    from zoo_mcp import kittycad_client

    kittycad_client.headers["Cache-Control"] = "no-cache"

    prompt = "Create a 10x10x10 cube."
    response = await mcp.call_tool("text_to_cad", arguments={"prompt": prompt})
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "/*\nGenerated by Text-to-CAD" in result
    assert "Text-To-CAD reasoning complete." in caplog.text


@pytest.mark.asyncio
@pytest.mark.flaky(reruns=3, reruns_delay=1)
async def test_edit_kcl_project_success(kcl_project: str, caplog):
    import logging

    caplog.set_level(logging.INFO)
    from zoo_mcp import kittycad_client

    kittycad_client.headers["Cache-Control"] = "no-cache"

    prompt = "make the bench longer"
    response = await mcp.call_tool(
        "edit_kcl_project",
        arguments={
            "proj_path": kcl_project,
            "prompt": prompt,
        },
    )

    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, dict)
    assert "main.kcl" in result.keys()
    assert "bench-parts.kcl" in result.keys()
    assert "subdir/main.kcl" in result.keys()
    assert "Text-To-CAD reasoning complete." in caplog.text


@pytest.mark.asyncio
async def test_edit_kcl_project_error(kcl_project: str):
    prompt = "the quick brown fox jumps over the lazy dog"
    response = await mcp.call_tool(
        "edit_kcl_project",
        arguments={
            "proj_path": kcl_project,
            "prompt": prompt,
        },
    )

    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, str)
    assert "400 Bad Request" in result


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


def test_check_kcl_code_or_path_nonexistent_path():
    """Test that providing a nonexistent path raises an exception."""
    with pytest.raises(ZooMCPException) as exc_info:
        _check_kcl_code_or_path(kcl_code=None, kcl_path="/nonexistent/path/to/file.kcl")
    assert "does not exist" in str(exc_info.value)
