import json
from collections.abc import Sequence
from pathlib import Path

import pytest
import pytest_asyncio
from mcp.types import ImageContent, TextContent

from zoo_mcp.kcl_docs import KCLDocs
from zoo_mcp.kcl_samples import KCLSamples
from zoo_mcp.server import mcp


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
async def test_calculate_volume_uppercase_step_extension(cube2_step_uppercase: str):
    """Test that CAD files with uppercase extensions (e.g., .STEP) are handled correctly."""
    response = await mcp.call_tool(
        "calculate_volume",
        arguments={"input_file": cube2_step_uppercase, "unit_volume": "cm3"},
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, float)
    # The cube2.STEP file should have a valid volume
    assert result > 0


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
async def test_multi_isometric_snapshot_of_cad(cube_stl: str):
    response = await mcp.call_tool(
        "multi_isometric_snapshot_of_cad",
        arguments={
            "input_file": cube_stl,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[0], list)
    result = response[0][0]
    assert isinstance(result, ImageContent)


@pytest.mark.asyncio
async def test_multi_isometric_snapshot_of_cad_error(empty_step: str):
    response = await mcp.call_tool(
        "multi_isometric_snapshot_of_cad",
        arguments={
            "input_file": empty_step,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "error creating the multi-isometric snapshot" in result


@pytest.mark.asyncio
async def test_multi_isometric_snapshot_of_kcl(cube_kcl: str):
    response = await mcp.call_tool(
        "multi_isometric_snapshot_of_kcl",
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
async def test_multi_isometric_snapshot_of_kcl_error(empty_step: str):
    response = await mcp.call_tool(
        "multi_isometric_snapshot_of_kcl",
        arguments={
            "kcl_code": None,
            "kcl_path": empty_step,
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "error creating the multi-isometric snapshot" in result


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
async def test_text_to_cad_success():
    from zoo_mcp import kittycad_client

    kittycad_client.headers["Cache-Control"] = "no-cache"

    prompt = "Create a cube centered at the origin with side length 10mm."
    response = await mcp.call_tool("text_to_cad", arguments={"prompt": prompt})
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "/*\nGenerated by Text-to-CAD" in result


@pytest.mark.asyncio
@pytest.mark.flaky(reruns=3, reruns_delay=1)
async def test_edit_kcl_project_success(kcl_project: str):
    from zoo_mcp import kittycad_client

    kittycad_client.headers["Cache-Control"] = "no-cache"

    prompt = "make the bench length 60mm"
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


@pytest_asyncio.fixture(scope="module")
async def live_docs_cache():
    """Initialize documentation cache from live GitHub data.

    This fixture fetches real documentation from GitHub once per test module,
    providing a more realistic test of the documentation system.
    """
    # Reset singleton to ensure fresh initialization in this worker
    KCLDocs._instance = None

    # Initialize the docs cache from GitHub
    await KCLDocs.initialize()

    # Verify docs were fetched
    assert KCLDocs._instance is not None, "Docs cache should be initialized"
    assert len(KCLDocs._instance.docs) > 0, "Should have fetched some docs"

    yield KCLDocs._instance


@pytest.mark.xdist_group(name="docs")
@pytest.mark.asyncio
async def test_list_kcl_docs(live_docs_cache):
    """Test that list_kcl_docs returns categorized documentation."""
    response = await mcp.call_tool("list_kcl_docs", arguments={})
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) == 1
    assert isinstance(inner_list[0], TextContent)
    result = json.loads(inner_list[0].text)

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


@pytest.mark.xdist_group(name="docs")
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
    assert any("extrude" in p.lower() for p in paths), (
        "Should find extrude-related docs"
    )


@pytest.mark.xdist_group(name="docs")
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


@pytest.mark.xdist_group(name="docs")
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


@pytest.mark.xdist_group(name="docs")
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


@pytest.mark.xdist_group(name="docs")
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


@pytest.mark.xdist_group(name="docs")
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


@pytest.mark.xdist_group(name="docs")
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


@pytest.mark.xdist_group(name="docs")
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


@pytest_asyncio.fixture(scope="module")
async def live_samples_cache():
    """Initialize samples cache from live GitHub data.

    This fixture fetches the real samples manifest from GitHub once per test module,
    providing a more realistic test of the samples system.
    """
    # Reset singleton to ensure fresh initialization in this worker
    KCLSamples._instance = None

    # Initialize the samples cache from GitHub
    await KCLSamples.initialize()

    # Verify manifest was fetched
    assert KCLSamples._instance is not None, "Samples cache should be initialized"
    assert len(KCLSamples._instance.manifest) > 0, "Should have fetched manifest"

    yield KCLSamples._instance


@pytest.mark.xdist_group(name="samples")
@pytest.mark.asyncio
async def test_list_kcl_samples(live_samples_cache):
    """Test that list_kcl_samples returns sample information."""
    response = await mcp.call_tool("list_kcl_samples", arguments={})
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) > 100, "Should have many samples"

    # Parse first result and check structure
    first_result = json.loads(inner_list[0].text)
    assert "name" in first_result
    assert "title" in first_result
    assert "description" in first_result
    assert "multipleFiles" in first_result


@pytest.mark.xdist_group(name="samples")
@pytest.mark.asyncio
async def test_search_kcl_samples_gear(live_samples_cache):
    """Test searching for 'gear' returns relevant results."""
    response = await mcp.call_tool(
        "search_kcl_samples", arguments={"query": "gear", "max_results": 5}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) > 0, "Should find results for 'gear'"

    result = [json.loads(tc.text) for tc in inner_list]

    # Check result structure
    first_result = result[0]
    assert "name" in first_result
    assert "title" in first_result
    assert "description" in first_result
    assert "match_count" in first_result
    assert "excerpt" in first_result

    # Should find gear-related samples
    all_text = " ".join([r["title"] + r["description"] for r in result]).lower()
    assert "gear" in all_text, "Results should contain 'gear'"


@pytest.mark.xdist_group(name="samples")
@pytest.mark.asyncio
async def test_search_kcl_samples_bearing(live_samples_cache):
    """Test searching for 'bearing' returns relevant results."""
    response = await mcp.call_tool(
        "search_kcl_samples", arguments={"query": "bearing", "max_results": 5}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) > 0, "Should find results for 'bearing'"

    result = [json.loads(tc.text) for tc in inner_list]

    # Should find bearing-related samples
    names = [r["name"] for r in result]
    assert any("bearing" in n for n in names), "Should find bearing samples"


@pytest.mark.xdist_group(name="samples")
@pytest.mark.asyncio
async def test_search_kcl_samples_no_results(live_samples_cache):
    """Test that search_kcl_samples handles queries with no matches."""
    response = await mcp.call_tool(
        "search_kcl_samples",
        arguments={"query": "xyznonexistentterm12345abc", "max_results": 5},
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) == 0, "Should find no results for gibberish query"


@pytest.mark.xdist_group(name="samples")
@pytest.mark.asyncio
async def test_search_kcl_samples_empty_query(live_samples_cache):
    """Test that search_kcl_samples handles empty queries."""
    response = await mcp.call_tool(
        "search_kcl_samples", arguments={"query": "", "max_results": 5}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) == 1

    result = json.loads(inner_list[0].text)
    assert "error" in result


@pytest.mark.xdist_group(name="samples")
@pytest.mark.asyncio
async def test_get_kcl_sample_single_file(live_samples_cache):
    """Test that get_kcl_sample retrieves a single-file sample."""
    response = await mcp.call_tool(
        "get_kcl_sample", arguments={"sample_name": "ball-bearing"}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0
    assert isinstance(response[1], dict)
    result = response[1]["result"]

    assert isinstance(result, dict)
    assert result["name"] == "ball-bearing"
    assert "title" in result
    assert "description" in result
    assert "files" in result
    assert len(result["files"]) >= 1

    # Check file structure
    main_file = next((f for f in result["files"] if f["filename"] == "main.kcl"), None)
    assert main_file is not None, "Should have main.kcl"
    assert len(main_file["content"]) > 0, "Should have content"


@pytest.mark.xdist_group(name="samples")
@pytest.mark.asyncio
async def test_get_kcl_sample_multi_file(live_samples_cache):
    """Test that get_kcl_sample retrieves a multi-file sample."""
    response = await mcp.call_tool(
        "get_kcl_sample", arguments={"sample_name": "axial-fan"}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0
    assert isinstance(response[1], dict)
    result = response[1]["result"]

    assert isinstance(result, dict)
    assert result["name"] == "axial-fan"
    assert result["multipleFiles"] is True
    assert len(result["files"]) > 1, "Should have multiple files"

    # Check expected files exist
    filenames = [f["filename"] for f in result["files"]]
    assert "main.kcl" in filenames
    assert "parameters.kcl" in filenames or "fan.kcl" in filenames


@pytest.mark.xdist_group(name="samples")
@pytest.mark.asyncio
async def test_get_kcl_sample_not_found(live_samples_cache):
    """Test that get_kcl_sample handles missing samples."""
    response = await mcp.call_tool(
        "get_kcl_sample", arguments={"sample_name": "nonexistent-sample-xyz"}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) == 1

    result = inner_list[0].text
    assert isinstance(result, str)
    assert "Sample not found" in result


@pytest.mark.xdist_group(name="samples")
@pytest.mark.asyncio
async def test_get_kcl_sample_path_traversal(live_samples_cache):
    """Test that get_kcl_sample rejects path traversal attempts."""
    response = await mcp.call_tool(
        "get_kcl_sample", arguments={"sample_name": "../../../etc/passwd"}
    )
    assert isinstance(response, Sequence)
    assert len(response) > 0

    inner_list = response[0]
    assert isinstance(inner_list, list)
    assert len(inner_list) == 1

    result = inner_list[0].text
    assert isinstance(result, str)
    assert "Sample not found" in result


@pytest.mark.asyncio
async def test_save_image(cube_stl: str, tmp_path):
    """Test saving an image to disk."""
    # First get an image from snapshot_of_cad
    snapshot_response = await mcp.call_tool(
        "snapshot_of_cad",
        arguments={
            "input_file": cube_stl,
            "camera_view": "isometric",
        },
    )
    assert isinstance(snapshot_response, Sequence)
    assert isinstance(snapshot_response[0], list)
    image = snapshot_response[0][0]
    assert isinstance(image, ImageContent)

    # Now save the image to disk
    output_path = tmp_path / "test_image.png"
    response = await mcp.call_tool(
        "save_image",
        arguments={
            "image": image.model_dump(),
            "output_path": str(output_path),
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


@pytest.mark.asyncio
async def test_save_image_to_directory(cube_stl: str, tmp_path):
    """Test saving an image to a directory creates image.png."""
    # First get an image from snapshot_of_cad
    snapshot_response = await mcp.call_tool(
        "snapshot_of_cad",
        arguments={
            "input_file": cube_stl,
            "camera_view": "isometric",
        },
    )
    assert isinstance(snapshot_response, Sequence)
    assert isinstance(snapshot_response[0], list)
    image = snapshot_response[0][0]

    # Save to directory
    response = await mcp.call_tool(
        "save_image",
        arguments={
            "image": image.model_dump(),
            "output_path": str(tmp_path),
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert Path(result).exists()
    assert Path(result).name == "image.png"
    assert Path(result).stat().st_size > 0


@pytest.mark.asyncio
async def test_save_image_creates_parent_dirs(cube_stl: str, tmp_path):
    """Test that save_image creates parent directories if they don't exist."""
    # First get an image from snapshot_of_cad
    snapshot_response = await mcp.call_tool(
        "snapshot_of_cad",
        arguments={
            "input_file": cube_stl,
            "camera_view": "isometric",
        },
    )
    assert isinstance(snapshot_response, Sequence)
    assert isinstance(snapshot_response[0], list)
    image = snapshot_response[0][0]

    # Save to a nested path that doesn't exist
    output_path = tmp_path / "nested" / "dirs" / "test_image.png"
    response = await mcp.call_tool(
        "save_image",
        arguments={
            "image": image.model_dump(),
            "output_path": str(output_path),
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


@pytest.mark.asyncio
async def test_save_image_to_temp_file(cube_stl: str):
    """Test that save_image creates a temp file when no path is provided."""
    # First get an image from snapshot_of_cad
    snapshot_response = await mcp.call_tool(
        "snapshot_of_cad",
        arguments={
            "input_file": cube_stl,
            "camera_view": "isometric",
        },
    )
    assert isinstance(snapshot_response, Sequence)
    assert isinstance(snapshot_response[0], list)
    image = snapshot_response[0][0]

    # Save without specifying a path
    response = await mcp.call_tool(
        "save_image",
        arguments={
            "image": image.model_dump(),
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert Path(result).exists()
    assert Path(result).suffix == ".png"
    assert Path(result).stat().st_size > 0
