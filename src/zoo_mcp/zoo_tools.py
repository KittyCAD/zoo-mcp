import math
from pathlib import Path
from uuid import uuid4

from kittycad.models import (
    FileCenterOfMass,
    FileConversion,
    FileExportFormat,
    FileImportFormat,
    FileSurfaceArea,
    FileVolume,
    FileMass,
    ImageFormat,
    ImportFile,
    ModelingCmd,
    ModelingCmdId,
    Point3d,
    PostEffectType,
    UnitArea,
    UnitDensity,
    UnitLength,
    UnitMass,
    UnitVolume,
    WebSocketRequest,
)
from kittycad.models.modeling_cmd import (
    OptionDefaultCameraLookAt,
    OptionDefaultCameraSetOrthographic,
    OptionImportFiles,
    OptionTakeSnapshot,
    OptionViewIsometric,
    OptionZoomToFit,
)
from kittycad.models.web_socket_request import OptionModelingCmdReq
from kittycad import KittyCAD
import aiofiles
import kcl

from zoo_mcp import logger
from zoo_mcp.utils.image_utils import create_image_collage

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
) -> dict[str, float] | None:
    """Calculate the center of mass of the file

    Args:
        file_path(Path | str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_length(str): The unit length to return. This should be one of 'cm', 'ft', 'in', 'm', 'mm', 'yd'
        max_attempts(int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        dict[str] | None: If the center of mass can be calculated return the center of mass as a dictionary with x, y, and z keys, otherwise return None
    """
    file_path = Path(file_path)

    logger.info("Calculating center of mass for %s", str(file_path.resolve()))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
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
                return None

            com = (
                result.center_of_mass.to_dict()
                if result.center_of_mass is not None
                else None
            )

            return com

        except Exception as e:
            logger.error("Failed to calculate center of mass: %s", e)
            return None

    logger.critical("Failed to calculate center mass after %s attempts", max_attempts)
    return None


async def zoo_calculate_mass(
    file_path: Path | str,
    unit_mass: str,
    unit_density: str,
    density: float,
    max_attempts: int = 3,
) -> float | None:
    """Calculate the mass of the file in the requested unit

    Args:
        file_path(Path or str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_mass(str): The unit mass to return. This should be one of 'g', 'kg', 'lb'.
        unit_density(str): The unit density of the material. This should be one of 'lb:ft3', 'kg:m3'.
        density(float): The density of the material.
        max_attempts(int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        float | None: If the mass of the file can be calculated, return the mass in the requested unit, otherwise return None
    """

    file_path = Path(file_path)

    logger.info("Calculating mass for %s", str(file_path.resolve()))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
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
                return None

            mass = result.mass if result.mass is not None else math.nan

            return mass

        except Exception as e:
            logger.error("Failed to calculate mass: %s", e)
            return None

    logger.critical("Failed to calculate mass after %s attempts", max_attempts)
    return None


async def zoo_calculate_surface_area(
    file_path: Path | str, unit_area: str, max_attempts: int = 3
) -> float | None:
    """Calculate the surface area of the file in the requested unit

    Args:
        file_path (Path or str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_area (str): The unit area to return. This should be one of 'cm2', 'dm2', 'ft2', 'in2', 'km2', 'm2', 'mm2', 'yd2'.
        max_attempts (int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        float | None: If the surface area can be calculated return the surface area, otherwise return None
    """

    file_path = Path(file_path)

    logger.info("Calculating surface area for %s", str(file_path.resolve()))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
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
                    "Failed to calculate surface area, incorrect return type %s", type(result)
                )
                return None

            surface_area = (
                result.surface_area if result.surface_area is not None else math.nan
            )

            return surface_area

        except Exception as e:
            logger.error("Failed to calculate surface area: %s", e)
            return None

    logger.critical("Failed to calculate surface area after %s attempts", max_attempts)
    return None


async def zoo_calculate_volume(
    file_path: Path | str, unit_vol: str, max_attempts: int = 3
) -> float | None:
    """Calculate the volume of the file in the requested unit

    Args:
        file_path (Path or str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_vol (str): The unit volume to return. This should be one of 'cm3', 'ft3', 'in3', 'm3', 'yd3', 'usfloz', 'usgal', 'l', 'ml'.
        max_attempts(int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        float | None: If the volume of the file can be calculated, return the volume in the requested unit, otherwise return None
    """

    file_path = Path(file_path)

    logger.info("Calculating volume for %s", str(file_path.resolve()))

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
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
                return None

            volume = result.volume if result.volume is not None else math.nan

            return volume

        except Exception as e:
            logger.error("Failed to calculate volume: %s", e)
            return None

    logger.critical("Failed to calculate volume after %s attempts", max_attempts)
    return None


async def zoo_convert_cad_file(
    input_path: Path | str,
    export_path: Path | str | None,
    export_format: FileExportFormat | str | None = FileExportFormat.STEP,
    max_attempts: int = 3,
) -> Path | None:
    """Convert a cad file to another cad file

    Args:
        input_path (Path | str): path to the CAD file to convert. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        export_path (Path | str): The path to save the cad file. If no path is provided, a temporary file will be created. If the path is a directory, a temporary file will be created in the directory. If the path is a file, it will be overwritten if the extension is valid.
        export_format (FileExportFormat | str | None): format to export the KCL code to. This should be one of 'fbx', 'glb', 'gltf', 'obj', 'ply', 'step', 'stl'. If no format is provided, the default is 'step'.
        max_attempts (int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        Path | None: Return the path to the exported model if successful, otherwise return None
    """

    input_path = Path(input_path)
    input_ext = input_path.suffix.split(".")[1]
    if input_ext not in [i.value for i in FileImportFormat]:
        logger.error("The provided input path does not have a valid extension")
        return None
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
        try:
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
                return None

            if export_response.outputs is None:
                logger.error("Failed to convert file")
                return None

            async with aiofiles.open(export_path, "wb") as out:
                await out.write(list(export_response.outputs.values())[0])

            logger.info(
                "KCL project exported successfully to %s", str(export_path.resolve())
            )

            return export_path
        except Exception as e:
            logger.error("Failed to export step: %s", e)

            return None
    logger.critical("Failed to convert CAD file after %s attempts", max_attempts)
    return None


async def zoo_export_kcl(
    kcl_code: str | None,
    kcl_path: Path | str | None,
    export_path: Path | str | None,
    export_format: kcl.FileExportFormat | str | None = kcl.FileExportFormat.Step,
    max_attempts: int = 3,
) -> Path | None:
    """Export KCL code to a CAD file. Either kcl_code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file or a directory containing a main.kcl file.

    Args:
        kcl_code (str): KCL code
        kcl_path (Path | str): KCL path, the path should point to a .kcl file or a directory containing a main.kcl file.
        export_path (Path | str | None): path to save the step file, this should be a directory or a file with the appropriate extension. If no path is provided, a temporary file will be created.
        export_format (kcl.FileExportFormat | str | None): format to export the KCL code to. This should be one of 'fbx', 'glb', 'gltf', 'obj', 'ply', 'step', 'stl'. If no format is provided, the default is 'step'.
        max_attempts (int): number of attempts to convert code, default is 3. Sometimes engines may not be available so we retry.

    Returns:
        Path | None: Return the path to the exported model if successful, otherwise return None
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
            return None
        if kcl_path.is_dir() and not (kcl_path / "main.kcl").is_file():
            logger.error(
                "The provided kcl_path directory does not contain a main.kcl file"
            )
            return None

    if not kcl_code and not kcl_path:
        logger.error("Neither code nor kcl_path provided")
        return None

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
        try:
            if kcl_code:
                export_response = await kcl.execute_code_and_export(
                    kcl_code, export_format
                )
            else:
                assert isinstance(kcl_path, Path)
                export_response = await kcl.execute_and_export(
                    str(kcl_path.resolve()), export_format
                )

            async with aiofiles.open(export_path.name, "wb") as out:
                await out.write(bytes(export_response[0].contents))

            logger.info("KCL exported successfully to %s", str(export_path.name))

            return export_path
        except Exception as e:
            logger.error("Failed to export step: %s", e)

            return None

    logger.critical("Failed to export KCL after %s attempts", max_attempts)
    return None


async def zoo_multiview_snapshot_of_kcl(
    kcl_code: str | None,
    kcl_path: Path | str | None,
    padding: float = 0.2,
) -> bytes | None:
    """Execute the KCL code and save a multiview snapshot of the resulting CAD model. Either kcl_code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file or a directory containing a main.kcl file.

    Args:
        kcl_code (str): KCL code
        kcl_path (Path | str): KCL path, the path should point to a .kcl file or a directory containing a main.kcl file.
        padding (float): The padding to apply to the snapshot. Default is 0.2.

    Returns:
        bytes or None: The JPEG image contents if successful, or None if there was an error.
    """

    logger.info("Taking a multiview snapshot of KCL")

    # default to using the code if both are provided
    if kcl_code and kcl_path:
        logger.info("Both code and kcl_path provided, using code")
        kcl_path = None

    if kcl_path:
        kcl_path = Path(kcl_path)
        if kcl_path.is_file() and kcl_path.suffix != ".kcl":
            logger.info("The provided kcl_path is not a .kcl file")
            return None
        if kcl_path.is_dir() and not (kcl_path / "main.kcl").is_file():
            logger.info(
                "The provided kcl_path directory does not contain a main.kcl file"
            )
            return None

    if not kcl_code and not kcl_path:
        logger.info("Neither code nor kcl_path provided")
        return None

    try:
        # None in the camera list means isometric view
        # https://github.com/KittyCAD/modeling-app/blob/main/rust/kcl-python-bindings/tests/tests.py#L192
        camera_list = [
            kcl.CameraLookAt(
                up=kcl.Point3d(x=0, y=0, z=1),
                vantage=kcl.Point3d(x=0, y=-1, z=0),
                center=kcl.Point3d(x=0, y=0, z=0),
            ),
            kcl.CameraLookAt(
                up=kcl.Point3d(x=0, y=0, z=1),
                vantage=kcl.Point3d(x=1, y=0, z=0),
                center=kcl.Point3d(x=0, y=0, z=0),
            ),
            kcl.CameraLookAt(
                up=kcl.Point3d(x=0, y=1, z=0),
                vantage=kcl.Point3d(x=0, y=0, z=1),
                center=kcl.Point3d(x=0, y=0, z=0),
            ),
            None,
        ]

        views = [
            kcl.SnapshotOptions(camera=camera, padding=padding)
            for camera in camera_list
        ]

        if kcl_code:
            jpeg_contents_list = await kcl.execute_code_and_snapshot_views(
                kcl_code, kcl.ImageFormat.Jpeg, snapshot_options=views
            )
        else:
            assert isinstance(kcl_path, Path)
            jpeg_contents_list = await kcl.execute_and_snapshot_views(
                str(kcl_path), kcl.ImageFormat.Jpeg, snapshot_options=views
            )

        assert isinstance(jpeg_contents_list, list)
        for byte_obj in jpeg_contents_list:
            assert isinstance(byte_obj, bytes)
        collage = create_image_collage(jpeg_contents_list)

        return collage

    except Exception as e:
        logger.error("Failed to take multiview snapshot: %s", e)
        return None


def zoo_multiview_snapshot_of_cad(
    input_path: Path | str,
    padding: float = 0.2,
) -> bytes | None:
    """Save a multiview snapshot of a CAD file.

    Args:
        input_path (Path | str): Path to the CAD file to save a multiview snapshot. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        padding (float): The padding to apply to the snapshot. Default is 0.2.

    Returns:
        bytes or None: The JPEG image contents if successful, or None if there was an error.
    """

    input_path = Path(input_path)

    # Connect to the websocket.
    with (
        kittycad_client.modeling.modeling_commands_ws(
            fps=30,
            post_effect=PostEffectType.SSAO,
            show_grid=False,
            unlocked_framerate=False,
            video_res_height=1024,
            video_res_width=1024,
            webrtc=False,
        ) as ws,
        open(input_path, "rb") as data,
    ):
        # Import files request must be sent as binary, because the file contents might be binary.
        import_id = ModelingCmdId(uuid4())

        input_ext = input_path.suffix.split(".")[1]
        if input_ext not in [i.value for i in FileImportFormat]:
            logger.info("The provided input path does not have a valid extension")
            return None

        ws.send_binary(
            WebSocketRequest(
                OptionModelingCmdReq(
                    cmd=ModelingCmd(
                        OptionImportFiles(
                            files=[ImportFile(data=data.read(), path=str(input_path))],
                            format=FileImportFormat(input_ext),
                        )
                    ),
                    cmd_id=ModelingCmdId(import_id),
                )
            )
        )

        # Wait for the import to succeed.
        while True:
            message = ws.recv().model_dump()
            if message["request_id"] == import_id:
                break
        if message["success"] is not True:
            return None
        object_id = message["resp"]["data"]["modeling_response"]["data"]["object_id"]

        # set camera to ortho
        ortho_cam_id = ModelingCmdId(uuid4())
        ws.send(
            WebSocketRequest(
                OptionModelingCmdReq(
                    cmd=ModelingCmd(OptionDefaultCameraSetOrthographic()),
                    cmd_id=ModelingCmdId(ortho_cam_id),
                )
            )
        )

        views = [
            OptionDefaultCameraLookAt(
                up=Point3d(x=0, y=0, z=1),
                vantage=Point3d(x=0, y=-1, z=0),
                center=Point3d(x=0, y=0, z=0),
            ),
            OptionDefaultCameraLookAt(
                up=Point3d(x=0, y=0, z=1),
                vantage=Point3d(x=1, y=0, z=0),
                center=Point3d(x=0, y=0, z=0),
            ),
            OptionDefaultCameraLookAt(
                up=Point3d(x=0, y=1, z=0),
                vantage=Point3d(x=0, y=0, z=1),
                center=Point3d(x=0, y=0, z=0),
            ),
            OptionViewIsometric(),
        ]

        jpeg_contents_list = []

        for view in views:
            # change camera look at
            camera_look_id = ModelingCmdId(uuid4())
            ws.send(
                WebSocketRequest(
                    OptionModelingCmdReq(
                        cmd=ModelingCmd(view),
                        cmd_id=ModelingCmdId(camera_look_id),
                    )
                )
            )

            focus_id = ModelingCmdId(uuid4())
            ws.send(
                WebSocketRequest(
                    OptionModelingCmdReq(
                        cmd=ModelingCmd(
                            OptionZoomToFit(object_ids=[object_id], padding=padding)
                        ),
                        cmd_id=ModelingCmdId(focus_id),
                    )
                )
            )

            # Wait for success message.
            while True:
                message = ws.recv().model_dump()
                if message["request_id"] == focus_id:
                    break
            if message["success"] is not True:
                return None

            # Take a snapshot as a JPEG.
            snapshot_id = ModelingCmdId(uuid4())
            ws.send(
                WebSocketRequest(
                    OptionModelingCmdReq(
                        cmd=ModelingCmd(OptionTakeSnapshot(format=ImageFormat.JPEG)),
                        cmd_id=ModelingCmdId(snapshot_id),
                    )
                )
            )

            # Wait for success message.
            while True:
                message = ws.recv().model_dump()
                if message["request_id"] == snapshot_id:
                    break
            if message["success"] is not True:
                return None
            jpeg_contents = message["resp"]["data"]["modeling_response"]["data"][
                "contents"
            ]

            jpeg_contents_list.append(jpeg_contents)

        collage = create_image_collage(jpeg_contents_list)

        return collage


async def zoo_snapshot_of_kcl(
    kcl_code: str | None,
    kcl_path: Path | str | None,
    camera: kcl.CameraLookAt | None = None,
    padding: float = 0.2,
) -> bytes | None:
    """Execute the KCL code and save a single view snapshot of the resulting CAD model. Either kcl_code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file or a directory containing a main.kcl file.

    Args:
        kcl_code (str): KCL code
        kcl_path (Path | str): KCL path, the path should point to a .kcl file or a directory containing a main.kcl file.
        camera (kcl.CameraLookAt | None): The camera to use for the snapshot. If None, a default camera (isometric) will be used.
        padding (float): The padding to apply to the snapshot. Default is 0.2.

    Returns:
        bytes or None: The JPEG image contents if successful, or None if there was an error.
    """

    logger.info("Taking a snapshot of KCL")

    # default to using the code if both are provided
    if kcl_code and kcl_path:
        logger.info("Both code and kcl_path provided, using code")
        kcl_path = None

    if kcl_path:
        kcl_path = Path(kcl_path)
        if kcl_path.is_file() and kcl_path.suffix != ".kcl":
            logger.info("The provided kcl_path is not a .kcl file")
            return None
        if kcl_path.is_dir() and not (kcl_path / "main.kcl").is_file():
            logger.info(
                "The provided kcl_path directory does not contain a main.kcl file"
            )
            return None

    if not kcl_code and not kcl_path:
        logger.info("Neither code nor kcl_path provided")
        return None

    try:
        view = kcl.SnapshotOptions(camera=camera, padding=padding)

        if kcl_code:
            jpeg_contents_list = await kcl.execute_code_and_snapshot_views(
                kcl_code, kcl.ImageFormat.Jpeg, snapshot_options=[view]
            )
        else:
            assert isinstance(kcl_path, Path)
            jpeg_contents_list = await kcl.execute_and_snapshot_views(
                str(kcl_path), kcl.ImageFormat.Jpeg, snapshot_options=[view]
            )

        assert isinstance(jpeg_contents_list, list)
        for byte_obj in jpeg_contents_list:
            assert isinstance(byte_obj, bytes)

    except Exception as e:
        logger.error("Failed to take snapshot: %s", e)
        return None


def zoo_snapshot_of_cad(
    input_path: Path | str,
    camera: OptionDefaultCameraLookAt | OptionViewIsometric | None = None,
    padding: float = 0.2,
) -> bytes | None:
    """Save a single view snapshot of a CAD file.

    Args:
        input_path (Path | str): Path to the CAD file to save a snapshot. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        camera (OptionDefaultCameraLookAt | None): The camera to use for the snapshot. If None, a default camera (isometric) will be used.
        padding (float): The padding to apply to the snapshot. Default is 0.2.

    Returns:
        bytes or None: The JPEG image contents if successful, or None if there was an error.
    """

    input_path = Path(input_path)

    # Connect to the websocket.
    with (
        kittycad_client.modeling.modeling_commands_ws(
            fps=30,
            post_effect=PostEffectType.SSAO,
            show_grid=False,
            unlocked_framerate=False,
            video_res_height=1024,
            video_res_width=1024,
            webrtc=False,
        ) as ws,
        open(input_path, "rb") as data,
    ):
        # Import files request must be sent as binary, because the file contents might be binary.
        import_id = ModelingCmdId(uuid4())

        input_ext = input_path.suffix.split(".")[1]
        if input_ext not in [i.value for i in FileImportFormat]:
            logger.info("The provided input path does not have a valid extension")
            return None

        ws.send_binary(
            WebSocketRequest(
                OptionModelingCmdReq(
                    cmd=ModelingCmd(
                        OptionImportFiles(
                            files=[ImportFile(data=data.read(), path=str(input_path))],
                            format=FileImportFormat(input_ext),
                        )
                    ),
                    cmd_id=ModelingCmdId(import_id),
                )
            )
        )

        # Wait for the import to succeed.
        while True:
            message = ws.recv().model_dump()
            if message["request_id"] == import_id:
                break
        if message["success"] is not True:
            return None
        object_id = message["resp"]["data"]["modeling_response"]["data"]["object_id"]

        # set camera to ortho
        ortho_cam_id = ModelingCmdId(uuid4())
        ws.send(
            WebSocketRequest(
                OptionModelingCmdReq(
                    cmd=ModelingCmd(OptionDefaultCameraSetOrthographic()),
                    cmd_id=ModelingCmdId(ortho_cam_id),
                )
            )
        )

        camera_look_id = ModelingCmdId(uuid4())
        if camera is None:
            camera = OptionViewIsometric()
        ws.send(
            WebSocketRequest(
                OptionModelingCmdReq(
                    cmd=ModelingCmd(camera),
                    cmd_id=ModelingCmdId(camera_look_id),
                )
            )
        )

        focus_id = ModelingCmdId(uuid4())
        ws.send(
            WebSocketRequest(
                OptionModelingCmdReq(
                    cmd=ModelingCmd(
                        OptionZoomToFit(object_ids=[object_id], padding=padding)
                    ),
                    cmd_id=ModelingCmdId(focus_id),
                )
            )
        )

        # Wait for success message.
        while True:
            message = ws.recv().model_dump()
            if message["request_id"] == focus_id:
                break
        if message["success"] is not True:
            return None

        # Take a snapshot as a JPEG.
        snapshot_id = ModelingCmdId(uuid4())
        ws.send(
            WebSocketRequest(
                OptionModelingCmdReq(
                    cmd=ModelingCmd(OptionTakeSnapshot(format=ImageFormat.JPEG)),
                    cmd_id=ModelingCmdId(snapshot_id),
                )
            )
        )

        # Wait for success message.
        while True:
            message = ws.recv().model_dump()
            if message["request_id"] == snapshot_id:
                break
        if message["success"] is not True:
            return None
        jpeg_contents = message["resp"]["data"]["modeling_response"]["data"]["contents"]

        return jpeg_contents
