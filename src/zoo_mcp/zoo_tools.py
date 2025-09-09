from pathlib import Path
import math

from kittycad.models import (
    FileSurfaceArea,
    FileVolume,
    FileMass,
    UnitArea,
    UnitDensity,
    UnitMass,
    UnitVolume,
)
from kittycad import KittyCAD
from kittycad.models.file_import_format import FileImportFormat
import aiofiles
import kcl

from zoo_mcp import logger

kittycad_client = KittyCAD()

_kittycad_area_map = {
    "cm2": UnitArea.CM2,
    "dm2": UnitArea.DM2,
    "ft2": UnitArea.FT2,
    "in2": UnitArea.IN2,
    "km2": UnitArea.KM2,
    "m2": UnitArea.M2,
    "mm2": UnitArea.MM2,
    "yd2": UnitArea.YD2,
}

_kittycad_density_map = {
    "lb:ft3": UnitDensity.LB_FT3,
    "kg:m3": UnitDensity.KG_M3,
}

_kittycad_format_map = {
    ".fbx": FileImportFormat.FBX,
    ".gltf": FileImportFormat.GLTF,
    ".obj": FileImportFormat.OBJ,
    ".ply": FileImportFormat.PLY,
    ".sldprt": FileImportFormat.SLDPRT,
    ".step": FileImportFormat.STEP,
    ".stp": FileImportFormat.STEP,
    ".stl": FileImportFormat.STL,
}

_kittycad_mass_map = {
    "g": UnitMass.G,
    "kg": UnitMass.KG,
    "lb": UnitMass.LB,
}

_kittycad_volume_map = {
    "cm3": UnitVolume.CM3,
    "ft3": UnitVolume.FT3,
    "in3": UnitVolume.IN3,
    "m3": UnitVolume.M3,
    "yd3": UnitVolume.YD3,
    "usfloz": UnitVolume.USFLOZ,
    "usgal": UnitVolume.USGAL,
    "l": UnitVolume.L,
    "ml": UnitVolume.ML,
}


async def _zoo_convert_code_to_step(
    code: str, export_path: Path | str | None, max_attempts: int = 3
) -> tuple[bool, Path | None]:
    """Convert KCL code to step

    Args:
        code(str): KCL code
        export_path(Path | str): path to save the step file
        max_attempts (int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        tuple[bool, Path | None]: True if successful along with the path to the exported model, false, None otherwise
    """

    logger.info("Exporting KCL to Step")
    if export_path is None:
        export_path = await aiofiles.tempfile.NamedTemporaryFile(
            delete=False, suffix=".step"
        )
        export_path = Path(export_path.name)
    else:
        export_path = Path(export_path)

    if export_path.suffix.lower() not in [".step", ".stp"]:
        return False, None

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            export_response = await kcl.execute_code_and_export(
                code, kcl.FileExportFormat.Step
            )

            async with aiofiles.open(export_path, "wb") as out:
                await out.write(bytes(export_response[0].contents))

            logger.info("KCL exported successfully to %s", str(export_path.resolve()))

            return True, export_path
        except Exception as e:
            logger.error("Failed to export step: %s", e)

            return False, None
    return False, None


async def _zoo_convert_file_to_step(
    proj_path: Path | str, export_path: Path | str | None, max_attempts: int = 3
) -> tuple[bool, Path | None]:
    """Convert KCL file or project to step

    Args:
        proj_path(Path | str): path to the KCL project. If the path is a directory, it should contain a main.kcl file, otherwise the path should point to a .kcl file
        export_path(Path | str): path to save the step file
        max_attempts (int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        tuple[bool, Path | None]: True if successful along with the path to the exported model, false, None otherwise
    """

    logger.info("Exporting KCL project to Step")
    proj_path = Path(proj_path)
    if export_path is None:
        export_path = await aiofiles.tempfile.NamedTemporaryFile(
            delete=False, suffix=".step"
        )
        export_path = Path(export_path.name)
    else:
        export_path = Path(export_path)

    if export_path.suffix.lower() not in [".step", ".stp"]:
        return False, None

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            export_response = await kcl.execute_and_export(
                str(proj_path.resolve()), kcl.FileExportFormat.Step
            )

            async with aiofiles.open(export_path, "wb") as out:
                await out.write(bytes(export_response[0].contents))

            logger.info(
                "KCL project exported successfully to %s", str(export_path.resolve())
            )

            return True, export_path
        except Exception as e:
            logger.error("Failed to export step: %s", e)

            return False, None
    return False, None


async def _zoo_get_mass(
    file_path: Path | str,
    unit_mass: str,
    unit_density: str,
    density: float,
    max_attempts: int = 3,
) -> tuple[bool, float]:
    """Get the mass of the file in the requested unit

    Args:
        file_path (Path or str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stp, .stl
        unit_mass (str): The unit mass to return. This should be one of 'g', 'kg', 'lb'.
        unit_density (str): The unit density of the material. This should be one of 'lb:ft3', 'kg:m3'.
        density (float): The density of the material.
        max_attempts (int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        tuple[bool, str]: If the mass of the file can be calculated, return true and the mass in the requested unit, otherwise return false and math.nan
    """

    file_path = Path(file_path)

    logger.info("Getting mass for %s", str(file_path.resolve()))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            async with aiofiles.open(file_path, "rb") as inp:
                data = await inp.read()

            src_format = _kittycad_format_map[file_path.suffix.lower()]

            result = kittycad_client.file.create_file_mass(
                output_unit=_kittycad_mass_map[unit_mass],
                src_format=src_format,
                body=data,
                material_density_unit=_kittycad_density_map[unit_density],
                material_density=density,
            )

            if not isinstance(result, FileMass):
                logger.info(
                    "Failed to get mass, incorrect return type %s", type(result)
                )
                return False, math.nan

            mass = result.mass if result.mass is not None else math.nan

            return True, mass

        except Exception as e:
            logger.info("Failed to get mass: %s", e)
            return False, math.nan

    logger.info("Failed to get mass after %s attempts", max_attempts)
    return False, math.nan


async def _zoo_get_surface_area(
    file_path: Path | str, unit_area: str, max_attempts: int = 3
) -> tuple[bool, float]:
    """Get the surface area of the file in the requested unit

    Args:
        file_path (Path or str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stp, .stl
        unit_area (str): The unit area to return. This should be one of 'cm2', 'dm2', 'ft2', 'in2', 'km2', 'm2', 'mm2', 'yd2'.
        max_attempts (int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        tuple[bool, str]: If the surface area can be calculated return True and the surface area, otherwise return False and math.nan
    """

    file_path = Path(file_path)

    logger.info("Getting surface area for %s", str(file_path.resolve()))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            async with aiofiles.open(file_path, "rb") as inp:
                data = await inp.read()

            src_format = _kittycad_format_map[file_path.suffix.lower()]

            result = kittycad_client.file.create_file_surface_area(
                output_unit=_kittycad_area_map[unit_area],
                src_format=src_format,
                body=data,
            )

            if not isinstance(result, FileSurfaceArea):
                logger.info(
                    "Failed to get surface area, incorrect return type %s", type(result)
                )
                return False, math.nan

            surface_area = (
                result.surface_area if result.surface_area is not None else math.nan
            )

            return True, surface_area

        except Exception as e:
            logger.info("Failed to get surface area: %s", e)
            return False, math.nan

    logger.info("Failed to get surface area after %s attempts", max_attempts)
    return False, math.nan


async def _zoo_get_volume(
    file_path: Path | str, unit_vol: str, max_attempts: int = 3
) -> tuple[bool, float]:
    """Get the volume of the file in the requested unit

    Args:
        file_path (Path or str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stp, .stl
        unit_vol (str): The unit volume to return. This should be one of 'cm3', 'ft3', 'in3', 'm3', 'yd3', 'usfloz', 'usgal', 'l', 'ml'.
        max_attempts(int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        tuple[bool, str]: If the volume of the file can be calculated, return true and the volume in the requested unit, otherwise return false and math.nan
    """

    file_path = Path(file_path)

    logger.info("Getting volume for %s", str(file_path.resolve()))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            async with aiofiles.open(file_path, "rb") as inp:
                data = await inp.read()

            src_format = _kittycad_format_map[file_path.suffix.lower()]

            result = kittycad_client.file.create_file_volume(
                output_unit=_kittycad_volume_map[unit_vol],
                src_format=src_format,
                body=data,
            )

            if not isinstance(result, FileVolume):
                logger.info(
                    "Failed to get volume, incorrect return type %s", type(result)
                )
                return False, math.nan

            volume = result.volume if result.volume is not None else math.nan

            return True, volume

        except Exception as e:
            logger.info("Failed to get volume: %s", e)
            return False, math.nan

    logger.info("Failed to get volume after %s attempts", max_attempts)
    return False, math.nan
