from pathlib import Path

import pytest

from zoo_mcp.zoo_tools import (
    _zoo_calculate_center_of_mass,
    _zoo_calculate_mass,
    _zoo_calculate_surface_area,
    _zoo_calculate_volume,
)


@pytest.mark.asyncio
async def test_calculate_center_of_mass():
    test_file = Path(__file__).parent / "data" / "cube.step"
    path = f"{test_file.resolve()}"

    com = await _zoo_calculate_center_of_mass(file_path=path, unit_length="mm")
    assert isinstance(com, dict)
    assert "x" in com and "y" in com and "z" in com
    assert com["x"] == pytest.approx(5.0)
    assert com["y"] == pytest.approx(5.0)
    assert com["z"] == pytest.approx(-5.0)


@pytest.mark.asyncio
async def test_calculate_mass():
    test_file = Path(__file__).parent / "data" / "cube.step"
    path = f"{test_file.resolve()}"

    mass = await _zoo_calculate_mass(
        file_path=path, unit_mass="g", unit_density="kg:m3", density=1000.0
    )
    assert isinstance(mass, float)
    assert mass == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_calculate_surface_area():
    test_file = Path(__file__).parent / "data" / "cube.step"
    path = f"{test_file.resolve()}"

    surface_area = await _zoo_calculate_surface_area(file_path=path, unit_area="mm2")
    assert isinstance(surface_area, float)
    assert surface_area == pytest.approx(600.0)


@pytest.mark.asyncio
async def test_calculate_volume():
    test_file = Path(__file__).parent / "data" / "cube.step"
    path = f"{test_file.resolve()}"

    volume = await _zoo_calculate_volume(file_path=path, unit_vol="cm3")
    assert isinstance(volume, float)
    assert volume == pytest.approx(1.0)
