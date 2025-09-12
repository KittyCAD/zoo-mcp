from pathlib import Path

from kittycad.models import (
    FileCenterOfMass,
    FileConversion,
    FileExportFormat,
    FileImportFormat,
    FileSurfaceArea,
    FileVolume,
    FileMass,
    UnitArea,
    UnitDensity,
    UnitLength,
    UnitMass,
    UnitVolume,
)
from kittycad import KittyCAD
import aiofiles
import kcl

from zoo_mcp import logger, ZooMCPException

kittycad_client = KittyCAD()

_kcl_export_format_map = {
    "fbx": kcl.FileExportFormat.Fbx,
    "gltf": kcl.FileExportFormat.Gltf,
    "glb": kcl.FileExportFormat.Glb,
    "obj": kcl.FileExportFormat.Obj,
    "ply": kcl.FileExportFormat.Ply,
    "step": kcl.FileExportFormat.Step,
    "stl": kcl.FileExportFormat.Stl,
}


async def zoo_calculate_center_of_mass(
    file_path: Path | str,
    unit_length: str,
    max_attempts: int = 3,
) -> dict[str, float]:
    """Calculate the center of mass of the file

    Args:
        file_path(Path | str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_length(str): The unit length to return. This should be one of 'cm', 'ft', 'in', 'm', 'mm', 'yd'
        max_attempts(int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        dict[str]: If the center of mass can be calculated return the center of mass as a dictionary with x, y, and z keys
    """
    file_path = Path(file_path)

    logger.info("Calculating center of mass for %s", str(file_path.resolve()))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        async with aiofiles.open(file_path, "rb") as inp:
            data = await inp.read()

        src_format = FileImportFormat(file_path.suffix.split(".")[1].lower())

        result = kittycad_client.file.create_file_center_of_mass(
            src_format=src_format,
            body=data,
            output_unit=UnitLength(unit_length),
        )

        if not isinstance(result, FileCenterOfMass):
            logger.info(
                "Failed to calculate center of mass, incorrect return type %s",
                type(result),
            )
            raise ZooMCPException(
                "Failed to calculate center of mass, incorrect return type %s",
                type(result),
            )

        com = (
            result.center_of_mass.to_dict()
            if result.center_of_mass is not None
            else None
        )

        if com is None:
            raise ZooMCPException(
                "Failed to calculate center of mass, no center of mass returned"
            )

        return com

    logger.critical("Failed to calculate center mass after %s attempts", max_attempts)
    raise ZooMCPException(
        "Failed to calculate center of mass after %s attempts", max_attempts
    )


async def zoo_calculate_mass(
    file_path: Path | str,
    unit_mass: str,
    unit_density: str,
    density: float,
    max_attempts: int = 3,
) -> float:
    """Calculate the mass of the file in the requested unit

    Args:
        file_path(Path or str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_mass(str): The unit mass to return. This should be one of 'g', 'kg', 'lb'.
        unit_density(str): The unit density of the material. This should be one of 'lb:ft3', 'kg:m3'.
        density(float): The density of the material.
        max_attempts(int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        float | None: If the mass of the file can be calculated, return the mass in the requested unit
    """

    file_path = Path(file_path)

    logger.info("Calculating mass for %s", str(file_path.resolve()))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        async with aiofiles.open(file_path, "rb") as inp:
            data = await inp.read()

        src_format = FileImportFormat(file_path.suffix.split(".")[1].lower())

        result = kittycad_client.file.create_file_mass(
            output_unit=UnitMass(unit_mass),
            src_format=src_format,
            body=data,
            material_density_unit=UnitDensity(unit_density),
            material_density=density,
        )

        if not isinstance(result, FileMass):
            logger.info(
                "Failed to calculate mass, incorrect return type %s", type(result)
            )
            raise ZooMCPException(
                "Failed to calculate mass, incorrect return type %s", type(result)
            )

        mass = result.mass

        if mass is None:
            raise ZooMCPException("Failed to calculate mass, no mass returned")

        return mass

    logger.critical("Failed to calculate mass after %s attempts", max_attempts)
    raise ZooMCPException("Failed to calculate mass after %s attempts", max_attempts)


async def zoo_calculate_surface_area(
    file_path: Path | str, unit_area: str, max_attempts: int = 3
) -> float:
    """Calculate the surface area of the file in the requested unit

    Args:
        file_path (Path or str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_area (str): The unit area to return. This should be one of 'cm2', 'dm2', 'ft2', 'in2', 'km2', 'm2', 'mm2', 'yd2'.
        max_attempts (int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        float: If the surface area can be calculated return the surface area
    """

    file_path = Path(file_path)

    logger.info("Calculating surface area for %s", str(file_path.resolve()))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        async with aiofiles.open(file_path, "rb") as inp:
            data = await inp.read()

        src_format = FileImportFormat(file_path.suffix.split(".")[1].lower())

        result = kittycad_client.file.create_file_surface_area(
            output_unit=UnitArea(unit_area),
            src_format=src_format,
            body=data,
        )

        if not isinstance(result, FileSurfaceArea):
            logger.info(
                "Failed to calculate surface area, incorrect return type %s",
                type(result),
            )
            raise ZooMCPException(
                "Failed to calculate surface area, incorrect return type %s",
            )

        surface_area = result.surface_area

        if surface_area is None:
            raise ZooMCPException(
                "Failed to calculate surface area, no surface area returned"
            )

        return surface_area

    logger.critical("Failed to calculate surface area after %s attempts", max_attempts)
    raise ZooMCPException(
        "Failed to calculate surface area after %s attempts", max_attempts
    )


async def zoo_calculate_volume(
    file_path: Path | str, unit_vol: str, max_attempts: int = 3
) -> float:
    """Calculate the volume of the file in the requested unit

    Args:
        file_path (Path or str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_vol (str): The unit volume to return. This should be one of 'cm3', 'ft3', 'in3', 'm3', 'yd3', 'usfloz', 'usgal', 'l', 'ml'.
        max_attempts(int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        float: If the volume of the file can be calculated, return the volume in the requested unit
    """

    file_path = Path(file_path)

    logger.info("Calculating volume for %s", str(file_path.resolve()))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        async with aiofiles.open(file_path, "rb") as inp:
            data = await inp.read()

        src_format = FileImportFormat(file_path.suffix.split(".")[1].lower())

        result = kittycad_client.file.create_file_volume(
            output_unit=UnitVolume(unit_vol),
            src_format=src_format,
            body=data,
        )

        if not isinstance(result, FileVolume):
            logger.info(
                "Failed to calculate volume, incorrect return type %s", type(result)
            )
            raise ZooMCPException(
                "Failed to calculate volume, incorrect return type %s", type(result)
            )

        volume = result.volume

        if volume is None:
            raise ZooMCPException("Failed to calculate volume, no volume returned")

        return volume

    logger.critical("Failed to calculate volume after %s attempts", max_attempts)
    raise ZooMCPException("Failed to calculate volume after %s attempts", max_attempts)


async def zoo_convert_cad_file(
    input_path: Path | str,
    export_path: Path | str | None,
    export_format: FileExportFormat | str | None = FileExportFormat.STEP,
    max_attempts: int = 3,
) -> Path:
    """Convert a cad file to another cad file

    Args:
        input_path (Path | str): path to the CAD file to convert. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        export_path (Path | str): The path to save the cad file. If no path is provided, a temporary file will be created. If the path is a directory, a temporary file will be created in the directory. If the path is a file, it will be overwritten if the extension is valid.
        export_format (FileExportFormat | str | None): format to export the KCL code to. This should be one of 'fbx', 'glb', 'gltf', 'obj', 'ply', 'step', 'stl'. If no format is provided, the default is 'step'.
        max_attempts (int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        Path: Return the path to the exported model if successful
    """

    input_path = Path(input_path)
    input_ext = input_path.suffix.split(".")[1]
    if input_ext not in [i.value for i in FileImportFormat]:
        logger.error("The provided input path does not have a valid extension")
        raise ZooMCPException("The provided input path does not have a valid extension")
    logger.info("Converting the cad file %s", str(input_path.resolve()))

    # check the export format
    if not export_format:
        logger.warning("No export format provided, defaulting to step")
        export_format = FileExportFormat.STEP
    else:
        if export_format not in FileExportFormat:
            logger.warning("Invalid export format provided, defaulting to step")
            export_format = FileExportFormat.STEP
        if isinstance(export_format, str):
            export_format = FileExportFormat(export_format)

    if export_path is None:
        logger.warning("No export path provided, creating a temporary file")
        export_path = await aiofiles.tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{export_format.value.lower()}"
        )
        export_path = Path(export_path.name)
    else:
        export_path = Path(export_path)
        if export_path.suffix:
            ext = export_path.suffix.split(".")[1]
            if ext not in [i.value for i in FileExportFormat]:
                logger.warning(
                    "The provided export path does not have a valid extension, using a temporary file instead"
                )
                export_path = await aiofiles.tempfile.NamedTemporaryFile(
                    dir=export_path.parent.resolve(),
                    delete=False,
                    suffix=f".{export_format.value.lower()}",
                )
            else:
                logger.warning("The provided export path is a file, overwriting")
        else:
            export_path = await aiofiles.tempfile.NamedTemporaryFile(
                dir=export_path.resolve(),
                delete=False,
                suffix=f".{export_format.value.lower()}",
            )
            logger.info("Using provided export path: %s", str(export_path.name))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        async with aiofiles.open(input_path, "rb") as inp:
            data = await inp.read()

        export_response = kittycad_client.file.create_file_conversion(
            src_format=FileImportFormat(input_ext),
            output_format=FileExportFormat(export_format),
            body=data,
        )

        if not isinstance(export_response, FileConversion):
            logger.error(
                "Failed to convert file, incorrect return type %s",
                type(export_response),
            )
            raise ZooMCPException(
                "Failed to convert file, incorrect return type %s",
            )

        if export_response.outputs is None:
            logger.error("Failed to convert file")
            raise ZooMCPException("Failed to convert file no output response")

        async with aiofiles.open(export_path, "wb") as out:
            await out.write(list(export_response.outputs.values())[0])

        logger.info(
            "KCL project exported successfully to %s", str(export_path.resolve())
        )

        return export_path

    logger.critical("Failed to convert CAD file after %s attempts", max_attempts)
    raise ZooMCPException("Failed to convert CAD file after %s attempts", max_attempts)


async def zoo_export_kcl(
    kcl_code: str | None,
    kcl_path: Path | str | None,
    export_path: Path | str | None,
    export_format: kcl.FileExportFormat | str | None = kcl.FileExportFormat.Step,
    max_attempts: int = 3,
) -> Path:
    """Export KCL code to a CAD file. Either code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file or a directory containing a main.kcl file.

    Args:
        kcl_code (str): KCL code
        kcl_path (Path | str): KCL path, the path should point to a .kcl file or a directory containing a main.kcl file.
        export_path (Path | str | None): path to save the step file, this should be a directory or a file with the appropriate extension. If no path is provided, a temporary file will be created.
        export_format (kcl.FileExportFormat | str | None): format to export the KCL code to. This should be one of 'fbx', 'glb', 'gltf', 'obj', 'ply', 'step', 'stl'. If no format is provided, the default is 'step'.
        max_attempts (int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        Path: Return the path to the exported model if successful
    """

    logger.info("Exporting KCL to Step")

    # default to using the code if both are provided
    if kcl_code and kcl_path:
        logger.warning("Both code and kcl_path provided, using code")
        kcl_path = None

    if kcl_path:
        kcl_path = Path(kcl_path)
        if kcl_path.is_file() and kcl_path.suffix != ".kcl":
            logger.error("The provided kcl_path is not a .kcl file")
            raise ZooMCPException("The provided kcl_path is not a .kcl file")
        if kcl_path.is_dir() and not (kcl_path / "main.kcl").is_file():
            logger.error(
                "The provided kcl_path directory does not contain a main.kcl file"
            )
            raise ZooMCPException(
                "The provided kcl_path does not contain a main.kcl file"
            )

    if not kcl_code and not kcl_path:
        logger.error("Neither code nor kcl_path provided")
        raise ZooMCPException("Neither code nor kcl_path provided")

    # check the export format
    if not export_format:
        logger.warning("No export format provided, defaulting to step")
        export_format = kcl.FileExportFormat.Step
    else:
        if export_format not in _kcl_export_format_map.values():
            logger.warning("Invalid export format provided, defaulting to step")
            export_format = kcl.FileExportFormat.Step
        if isinstance(export_format, str):
            export_format = _kcl_export_format_map[export_format]

    if export_path is None:
        logger.warning("No export path provided, creating a temporary file")
        export_path = await aiofiles.tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{str(export_format).split('.')[1].lower()}"
        )
        export_path = Path(export_path.name)
    else:
        export_path = Path(export_path)
        if export_path.suffix:
            ext = export_path.suffix.split(".")[1]
            if ext not in [i.value for i in FileExportFormat]:
                logger.warning(
                    "The provided export path does not have a valid extension, using a temporary file instead"
                )
                export_path = await aiofiles.tempfile.NamedTemporaryFile(
                    dir=export_path.parent.resolve(),
                    delete=False,
                    suffix=f".{str(export_format).split('.')[1].lower()}",
                )
            else:
                logger.warning("The provided export path is a file, overwriting")
        else:
            export_path = await aiofiles.tempfile.NamedTemporaryFile(
                dir=export_path.resolve(),
                delete=False,
                suffix=f".{str(export_format).split('.')[1].lower()}",
            )
            logger.info("Using provided export path: %s", str(export_path.name))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        if kcl_code:
            logger.info("Exporting KCL code to %s", str(kcl_code))
            export_response = await kcl.execute_code_and_export(kcl_code, export_format)
        else:
            logger.info("Exporting KCL project to %s", str(kcl_path))
            assert isinstance(kcl_path, Path)
            export_response = await kcl.execute_and_export(
                str(kcl_path.resolve()), export_format
            )

        async with aiofiles.open(export_path.name, "wb") as out:
            await out.write(bytes(export_response[0].contents))

        logger.info("KCL exported successfully to %s", str(export_path.name))

        return export_path

    logger.critical("Failed to export KCL after %s attempts", max_attempts)
    raise ZooMCPException("Failed to export KCL after %s attempts", max_attempts)
