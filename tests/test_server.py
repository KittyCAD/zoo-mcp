from collections.abc import Sequence
from pathlib import Path

import aiofiles
import pytest

from zoo_mcp.server import mcp


@pytest.mark.asyncio
async def test_calculate_center_of_mass():
    test_file = Path(__file__).parent / "data" / "cube.stl"
    path = f"{test_file.resolve()}"

    response = await mcp.call_tool(
        "calculate_center_of_mass",
        arguments={
            "input_file": path,
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
async def test_calculate_center_of_mass_error():
    test_file = Path(__file__).parent / "data" / "cube.stl"
    path = f"{test_file.resolve()}"
    response = await mcp.call_tool(
        "calculate_center_of_mass",
        arguments={
            "input_file": path,
            "unit_length": "asdf",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "not a valid UnitLength" in result


@pytest.mark.asyncio
async def test_calculate_mass():
    test_file = Path(__file__).parent / "data" / "cube.stl"
    path = f"{test_file.resolve()}"

    response = await mcp.call_tool(
        "calculate_mass",
        arguments={
            "input_file": path,
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
async def test_calculate_mass_error():
    test_file = Path(__file__).parent / "data" / "cube.stl"
    path = f"{test_file.resolve()}"

    response = await mcp.call_tool(
        "calculate_mass",
        arguments={
            "input_file": path,
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
async def test_calculate_surface_area():
    test_file = Path(__file__).parent / "data" / "cube.stl"
    path = f"{test_file.resolve()}"

    response = await mcp.call_tool(
        "calculate_surface_area", arguments={"input_file": path, "unit_area": "mm2"}
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, float)
    assert result == pytest.approx(600.0)


@pytest.mark.asyncio
async def test_calculate_surface_area_error():
    test_file = Path(__file__).parent / "data" / "cube.step"
    path = f"{test_file.resolve()}"

    response = await mcp.call_tool(
        "calculate_surface_area",
        arguments={
            "input_file": path,
            "unit_area": "asdf",
        },
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "not a valid UnitArea" in result


@pytest.mark.asyncio
async def test_calculate_volume():
    test_file = Path(__file__).parent / "data" / "cube.step"
    path = f"{test_file.resolve()}"

    response = await mcp.call_tool(
        "calculate_volume", arguments={"input_file": path, "unit_volume": "cm3"}
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert isinstance(result, float)
    assert result == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_calculate_volume_error():
    test_file = Path(__file__).parent / "data" / "cube.step"
    path = f"{test_file.resolve()}"

    response = await mcp.call_tool(
        "calculate_volume", arguments={"input_file": path, "unit_volume": "asdf"}
    )
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "not a valid UnitVolume" in result


@pytest.mark.asyncio
async def test_convert_cad_file():
    test_file = Path(__file__).parent / "data" / "cube.step"

    async with aiofiles.tempfile.NamedTemporaryFile(suffix=".obj", delete=False) as tmp:
        path = f"{test_file.resolve()}"
        export_path = f"{tmp.name}"
        response = await mcp.call_tool(
            "convert_cad_file",
            arguments={
                "input_path": path,
                "export_path": export_path,
                "export_format": "obj",
            },
        )
        assert isinstance(response, Sequence)
        assert isinstance(response[1], dict)
        result = response[1]["result"]
        assert Path(result).exists()
        assert Path(result).stat().st_size != 0

        # Clean up
        Path(tmp.name).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_convert_cad_file_error():
    test_file = Path(__file__).parent / "data" / "cube.step"

    async with aiofiles.tempfile.NamedTemporaryFile(
        suffix=".asdf", delete=False
    ) as tmp:
        path = f"{test_file.resolve()}"
        export_path = f"{tmp.name}"
        response = await mcp.call_tool(
            "convert_cad_file",
            arguments={
                "input_path": path,
                "export_path": export_path,
                "export_format": "asdf",
            },
        )
        assert isinstance(response, Sequence)
        assert isinstance(response[1], dict)
        result = response[1]["result"]
        assert "error converting the CAD" in result

        # Clean up
        Path(tmp.name).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_export_kcl():
    async with aiofiles.open(
        Path(__file__).parent / "data" / "cube.kcl", mode="r"
    ) as f:
        kcl_code = await f.read()

    async with aiofiles.tempfile.TemporaryDirectory() as tmp:
        response = await mcp.call_tool(
            "export_kcl",
            arguments={
                "kcl_code": kcl_code,
                "kcl_path": None,
                "export_path": tmp,
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
    async with aiofiles.tempfile.TemporaryDirectory() as tmp:
        response = await mcp.call_tool(
            "export_kcl",
            arguments={
                "kcl_code": "asdf",
                "kcl_path": None,
                "export_path": tmp,
                "export_format": "step",
            },
        )
        assert isinstance(response, Sequence)
        assert isinstance(response[1], dict)
        result = response[1]["result"]
        assert "error exporting the CAD" in result


@pytest.mark.asyncio
async def test_text_to_cad_success():
    prompt = "Create a 10x10x10 cube."
    response = await mcp.call_tool("text_to_cad", arguments={"prompt": prompt})
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "/*\nGenerated by Text-to-CAD" in result


@pytest.mark.asyncio
async def test_text_to_cad_failure():
    prompt = "the quick brown fox jumps over the lazy dog"
    response = await mcp.call_tool("text_to_cad", arguments={"prompt": prompt})
    assert isinstance(response, Sequence)
    assert isinstance(response[1], dict)
    result = response[1]["result"]
    assert "400 Bad Request" in result
