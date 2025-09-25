from enum import Enum
from pathlib import Path
from uuid import uuid4

import aiofiles
import kcl
from kittycad.models import (
    Axis,
    AxisDirectionPair,
    Direction,
    FileCenterOfMass,
    FileConversion,
    FileExportFormat,
    FileImportFormat,
    FileMass,
    FileSurfaceArea,
    FileVolume,
    ImageFormat,
    ImportFile,
    InputFormat3d,
    ModelingCmd,
    ModelingCmdId,
    Point3d,
    PostEffectType,
    System,
    UnitArea,
    UnitDensity,
    UnitLength,
    UnitMass,
    UnitVolume,
    WebSocketRequest,
)
from kittycad.models.input_format3d import (
    OptionFbx,
    OptionGltf,
    OptionObj,
    OptionPly,
    OptionSldprt,
    OptionStep,
    OptionStl,
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

from zoo_mcp import ZooMCPException, kittycad_client, logger
from zoo_mcp.utils.image_utils import create_image_collage


class KCLExportFormat(Enum):
    formats = {
        "fbx": kcl.FileExportFormat.Fbx,
        "gltf": kcl.FileExportFormat.Gltf,
        "glb": kcl.FileExportFormat.Glb,
        "obj": kcl.FileExportFormat.Obj,
        "ply": kcl.FileExportFormat.Ply,
        "step": kcl.FileExportFormat.Step,
        "stl": kcl.FileExportFormat.Stl,
    }


class CameraView(Enum):
    views = {
        "front": {"up": [0, 0, 1], "vantage": [0, -1, 0], "center": [0, 0, 0]},
        "back": {"up": [0, 0, 1], "vantage": [0, 1, 0], "center": [0, 0, 0]},
        "left": {"up": [0, 0, 1], "vantage": [-1, 0, 0], "center": [0, 0, 0]},
        "right": {"up": [0, 0, 1], "vantage": [1, 0, 0], "center": [0, 0, 0]},
        "top": {"up": [0, 1, 0], "vantage": [0, 0, 1], "center": [0, 0, 0]},
        "bottom": {"up": [0, -1, 0], "vantage": [0, 0, -1], "center": [0, 0, 0]},
    }

    @staticmethod
    def to_kcl_camera(view: dict[str, list[float]]) -> kcl.CameraLookAt:
        return kcl.CameraLookAt(
            up=kcl.Point3d(
                x=view["up"][0],
                y=view["up"][1],
                z=view["up"][2],
            ),
            vantage=kcl.Point3d(
                x=view["vantage"][0],
                y=-view["vantage"][1],
                z=view["vantage"][2],
            ),
            center=kcl.Point3d(
                x=view["center"][0],
                y=view["center"][1],
                z=view["center"][2],
            ),
        )

    @staticmethod
    def to_kittycad_camera(view: dict[str, list[float]]) -> OptionDefaultCameraLookAt:
        return OptionDefaultCameraLookAt(
            up=Point3d(
                x=view["up"][0],
                y=view["up"][1],
                z=view["up"][2],
            ),
            vantage=Point3d(
                x=view["vantage"][0],
                y=-view["vantage"][1],
                z=view["vantage"][2],
            ),
            center=Point3d(
                x=view["center"][0],
                y=view["center"][1],
                z=view["center"][2],
            ),
        )


def _get_input_format(ext: str) -> InputFormat3d | None:
    match ext.lower():
        case "fbx":
            return InputFormat3d(OptionFbx())
        case "gltf":
            return InputFormat3d(OptionGltf())
        case "obj":
            return InputFormat3d(
                OptionObj(
                    coords=System(
                        forward=AxisDirectionPair(
                            axis=Axis.Y, direction=Direction.NEGATIVE
                        ),
                        up=AxisDirectionPair(axis=Axis.Z, direction=Direction.POSITIVE),
                    ),
                    units=UnitLength.MM,
                )
            )
        case "ply":
            return InputFormat3d(
                OptionPly(
                    coords=System(
                        forward=AxisDirectionPair(
                            axis=Axis.Y, direction=Direction.NEGATIVE
                        ),
                        up=AxisDirectionPair(axis=Axis.Z, direction=Direction.POSITIVE),
                    ),
                    units=UnitLength.MM,
                )
            )
        case "sldprt":
            return InputFormat3d(OptionSldprt(split_closed_faces=True))
        case "step" | "stp":
            return InputFormat3d(OptionStep(split_closed_faces=True))
        case "stl":
            return InputFormat3d(
                OptionStl(
                    coords=System(
                        forward=AxisDirectionPair(
                            axis=Axis.Y, direction=Direction.NEGATIVE
                        ),
                        up=AxisDirectionPair(axis=Axis.Z, direction=Direction.POSITIVE),
                    ),
                    units=UnitLength.MM,
                )
            )
    return None


async def zoo_calculate_center_of_mass(
    file_path: Path | str,
    unit_length: str,
) -> dict[str, float]:
    """Calculate the center of mass of the file

    Args:
        file_path(Path | str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_length(str): The unit length to return. This should be one of 'cm', 'ft', 'in', 'm', 'mm', 'yd'

    Returns:
        dict[str]: If the center of mass can be calculated return the center of mass as a dictionary with x, y, and z keys
    """
    file_path = Path(file_path)

    logger.info("Calculating center of mass for %s", str(file_path.resolve()))

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

    com = result.center_of_mass.to_dict() if result.center_of_mass is not None else None

    if com is None:
        raise ZooMCPException(
            "Failed to calculate center of mass, no center of mass returned"
        )

    return com


async def zoo_calculate_mass(
    file_path: Path | str,
    unit_mass: str,
    unit_density: str,
    density: float,
) -> float:
    """Calculate the mass of the file in the requested unit

    Args:
        file_path(Path | str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_mass(str): The unit mass to return. This should be one of 'g', 'kg', 'lb'.
        unit_density(str): The unit density of the material. This should be one of 'lb:ft3', 'kg:m3'.
        density(float): The density of the material.

    Returns:
        float | None: If the mass of the file can be calculated, return the mass in the requested unit
    """

    file_path = Path(file_path)

    logger.info("Calculating mass for %s", str(file_path.resolve()))

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
        logger.info("Failed to calculate mass, incorrect return type %s", type(result))
        raise ZooMCPException(
            "Failed to calculate mass, incorrect return type %s", type(result)
        )

    mass = result.mass

    if mass is None:
        raise ZooMCPException("Failed to calculate mass, no mass returned")

    return mass


async def zoo_calculate_surface_area(file_path: Path | str, unit_area: str) -> float:
    """Calculate the surface area of the file in the requested unit

    Args:
        file_path (Path | str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_area (str): The unit area to return. This should be one of 'cm2', 'dm2', 'ft2', 'in2', 'km2', 'm2', 'mm2', 'yd2'.

    Returns:
        float: If the surface area can be calculated return the surface area
    """

    file_path = Path(file_path)

    logger.info("Calculating surface area for %s", str(file_path.resolve()))

    async with aiofiles.open(file_path, "rb") as inp:
        data = await inp.read()

    src_format = FileImportFormat(file_path.suffix.split(".")[1].lower())

    result = kittycad_client.file.create_file_surface_area(
        output_unit=UnitArea(unit_area),
        src_format=src_format,
        body=data,
    )

    if not isinstance(result, FileSurfaceArea):
        logger.error(
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


async def zoo_calculate_volume(file_path: Path | str, unit_vol: str) -> float:
    """Calculate the volume of the file in the requested unit

    Args:
        file_path (Path | str): The path to the file. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_vol (str): The unit volume to return. This should be one of 'cm3', 'ft3', 'in3', 'm3', 'yd3', 'usfloz', 'usgal', 'l', 'ml'.

    Returns:
        float: If the volume of the file can be calculated, return the volume in the requested unit
    """

    file_path = Path(file_path)

    logger.info("Calculating volume for %s", str(file_path.resolve()))

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


async def zoo_convert_cad_file(
    input_path: Path | str,
    export_path: Path | str | None = None,
    export_format: FileExportFormat | str | None = FileExportFormat.STEP,
) -> Path:
    """Convert a cad file to another cad file

    Args:
        input_path (Path | str): path to the CAD file to convert. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        export_path (Path | str | None): The path to save the cad file. If no path is provided, a temporary file will be created. If the path is a directory, a temporary file will be created in the directory. If the path is a file, it will be overwritten if the extension is valid.
        export_format (FileExportFormat | str | None): format to export the KCL code to. This should be one of 'fbx', 'glb', 'gltf', 'obj', 'ply', 'step', 'stl'. If no format is provided, the default is 'step'.

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
            logger.warning(
                "Invalid export format %s provided, defaulting to step", export_format
            )
            export_format = FileExportFormat.STEP
        else:
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

    logger.info("KCL project exported successfully to %s", str(export_path.resolve()))

    return export_path


async def zoo_export_kcl(
    kcl_code: str | None = None,
    kcl_path: Path | str | None = None,
    export_path: Path | str | None = None,
    export_format: kcl.FileExportFormat | str | None = kcl.FileExportFormat.Step,
) -> Path:
    """Export KCL code to a CAD file. Either kcl_code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file or a directory containing a main.kcl file.

    Args:
        kcl_code (str | None): KCL code
        kcl_path (Path | str | None): KCL path, the path should point to a .kcl file or a directory containing a main.kcl file.
        export_path (Path | str | None): path to save the step file, this should be a directory or a file with the appropriate extension. If no path is provided, a temporary file will be created.
        export_format (kcl.FileExportFormat | str | None): format to export the KCL code to. This should be one of 'fbx', 'glb', 'gltf', 'obj', 'ply', 'step', 'stl'. If no format is provided, the default is 'step'.

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
        if export_format not in KCLExportFormat.formats.value.keys():
            logger.warning(
                "Invalid export format %s provided, defaulting to step", export_format
            )
            export_format = kcl.FileExportFormat.Step
        else:
            export_format = KCLExportFormat.formats.value[export_format]

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

    async with aiofiles.open(export_path, "wb") as out:
        if kcl_code:
            logger.info("Exporting KCL code to %s", str(kcl_code))
            export_response = await kcl.execute_code_and_export(kcl_code, export_format)
        else:
            logger.info("Exporting KCL project to %s", str(kcl_path))
            assert isinstance(kcl_path, Path)
            export_response = await kcl.execute_and_export(
                str(kcl_path.resolve()), export_format
            )
        await out.write(bytes(export_response[0].contents))

    logger.info("KCL exported successfully to %s", str(export_path))
    return Path(export_path)


def zoo_multiview_snapshot_of_cad(
    input_path: Path | str,
    padding: float = 0.2,
) -> bytes:
    """Save a multiview snapshot of a CAD file.

    Args:
        input_path (Path | str): Path to the CAD file to save a multiview snapshot. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        padding (float): The padding to apply to the snapshot. Default is 0.2.

    Returns:
        bytes or None: The JPEG image contents if successful
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
            logger.error("The provided input path does not have a valid extension")
            raise ZooMCPException(
                "The provided input path does not have a valid extension"
            )

        input_format = _get_input_format(input_ext)
        if input_format is None:
            logger.error("The provided extension is not supported for import")
            raise ZooMCPException("The provided extension is not supported for import")

        ws.send_binary(
            WebSocketRequest(
                OptionModelingCmdReq(
                    cmd=ModelingCmd(
                        OptionImportFiles(
                            files=[ImportFile(data=data.read(), path=str(input_path))],
                            format=input_format,
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
            logger.error("Failed to import CAD file")
            raise ZooMCPException("Failed to import CAD file")
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
                logger.error("Failed to move camera to fit object")
                raise ZooMCPException("Failed to move camera to fit object")

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
                logger.error("Failed to capture snapshot")
                raise ZooMCPException("Failed to capture snapshot")
            jpeg_contents = message["resp"]["data"]["modeling_response"]["data"][
                "contents"
            ]

            jpeg_contents_list.append(jpeg_contents)

        collage = create_image_collage(jpeg_contents_list)

        return collage


async def zoo_multiview_snapshot_of_kcl(
    kcl_code: str | None,
    kcl_path: Path | str | None,
    padding: float = 0.2,
) -> bytes:
    """Execute the KCL code and save a multiview snapshot of the resulting CAD model. Either kcl_code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file or a directory containing a main.kcl file.

    Args:
        kcl_code (str | None): KCL code
        kcl_path (Path | str): KCL path, the path should point to a .kcl file or a directory containing a main.kcl file.
        padding (float): The padding to apply to the snapshot. Default is 0.2.

    Returns:
        bytes or None: The JPEG image contents if successful
    """

    logger.info("Taking a multiview snapshot of KCL")

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
        collage = create_image_collage(jpeg_contents_list)  # ty: ignore[invalid-argument-type]

        return collage

    except Exception as e:
        logger.error("Failed to take multiview snapshot: %s", e)
        raise ZooMCPException(f"Failed to take multiview snapshot: {e}")


def zoo_snapshot_of_cad(
    input_path: Path | str,
    camera: OptionDefaultCameraLookAt | OptionViewIsometric | None = None,
    padding: float = 0.2,
) -> bytes:
    """Save a single view snapshot of a CAD file.

    Args:
        input_path (Path | str): Path to the CAD file to save a snapshot. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        camera (OptionDefaultCameraLookAt | OptionViewIsometric | None): The camera to use for the snapshot. If None, a default camera (isometric) will be used.
        padding (float): The padding to apply to the snapshot. Default is 0.2.

    Returns:
        bytes or None: The JPEG image contents if successful
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
            logger.error("The provided input path does not have a valid extension")
            raise ZooMCPException(
                "The provided input path does not have a valid extension"
            )

        input_format = _get_input_format(input_ext)
        if input_format is None:
            logger.error("The provided extension is not supported for import")
            raise ZooMCPException("The provided extension is not supported for import")

        ws.send_binary(
            WebSocketRequest(
                OptionModelingCmdReq(
                    cmd=ModelingCmd(
                        OptionImportFiles(
                            files=[ImportFile(data=data.read(), path=str(input_path))],
                            format=input_format,
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
            raise ZooMCPException("Failed to import CAD file")
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
            raise ZooMCPException("Failed to zoom to fit on CAD file")

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
            raise ZooMCPException("Failed to take snapshot of CAD file")
        jpeg_contents = message["resp"]["data"]["modeling_response"]["data"]["contents"]

        return jpeg_contents


async def zoo_snapshot_of_kcl(
    kcl_code: str | None,
    kcl_path: Path | str | None,
    camera: kcl.CameraLookAt | None = None,
    padding: float = 0.2,
) -> bytes:
    """Execute the KCL code and save a single view snapshot of the resulting CAD model. Either kcl_code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file or a directory containing a main.kcl file.

    Args:
        kcl_code (str | None): KCL code
        kcl_path (Path | str | None): KCL path, the path should point to a .kcl file or a directory containing a main.kcl file.
        camera (kcl.CameraLookAt | None): The camera to use for the snapshot. If None, a default camera (isometric) will be used.
        padding (float): The padding to apply to the snapshot. Default is 0.2.

    Returns:
        bytes or None: The JPEG image contents if successful
    """

    logger.info("Taking a snapshot of KCL")

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

    return jpeg_contents_list[0]  # ty: ignore[invalid-return-type]
