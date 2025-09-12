import kcl
from kittycad.models.modeling_cmd import OptionDefaultCameraLookAt, Point3d
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent

from zoo_mcp import logger
from zoo_mcp.ai_tools import text_to_cad as _text_to_cad
from zoo_mcp.utils.image_utils import encode_image
from zoo_mcp.zoo_tools import (
    zoo_export_kcl,
    zoo_convert_cad_file,
    zoo_calculate_center_of_mass,
    zoo_calculate_mass,
    zoo_calculate_surface_area,
    zoo_calculate_volume,
    zoo_multiview_snapshot_of_cad,
    zoo_multiview_snapshot_of_kcl,
    zoo_snapshot_of_cad,
    zoo_snapshot_of_kcl,
)

mcp = FastMCP(
    name="Zoo MCP Server",
    log_level="WARNING",
)


@mcp.tool()
async def calculate_center_of_mass(input_file: str, unit_length: str) -> dict | str:
    """Calculate the center of mass of a 3d object represented by the input file.

    Args:
        input_file (str): The path of the file to get the mass from. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_length (str): The unit of length to return the result in. One of 'cm', 'ft', 'in', 'm', 'mm', 'yd'

    Returns:
        str: The center of mass of the file in the specified unit of length, or an error message if the operation fails.
    """

    logger.info("calculate_center_of_mass called for file: %s", input_file)

    try:
        com = await zoo_calculate_center_of_mass(
            file_path=input_file, unit_length=unit_length
        )
        return com
    except Exception as e:
        return f"There was an error calculating the center of mass of the file: {e}"


@mcp.tool()
async def calculate_mass(
    input_file: str, unit_mass: str, unit_density: str, density: float
) -> float | str:
    """Calculate the mass of a 3d object represented by the input file.

    Args:
        input_file (str): The path of the file to get the mass from. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_mass (str): The unit of mass to return the result in. One of 'g', 'kg', 'lb'.
        unit_density (str): The unit of density to calculate the mass. One of 'lb:ft3', 'kg:m3'.
        density (float): The density of the material.

    Returns:
        str: The mass of the file in the specified unit of mass, or an error message if the operation fails.
    """

    logger.info("calculate_mass called for file: %s", input_file)

    try:
        mass = await zoo_calculate_mass(
            file_path=input_file,
            unit_mass=unit_mass,
            unit_density=unit_density,
            density=density,
        )
        return mass
    except Exception as e:
        return f"There was an error calculating the mass of the file: {e}"


@mcp.tool()
async def calculate_surface_area(input_file: str, unit_area: str) -> float | str:
    """Calculate the surface area of a 3d object represented by the input file.

    Args:
        input_file (str): The path of the file to get the surface area from. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_area (str): The unit of area to return the result in. One of 'cm2', 'dm2', 'ft2', 'in2', 'km2', 'm2', 'mm2', 'yd2'.

    Returns:
        str: The surface area of the file in the specified unit of area, or an error message if the operation fails.
    """

    logger.info("calculate_surface_area called for file: %s", input_file)

    try:
        surface_area = await zoo_calculate_surface_area(
            file_path=input_file, unit_area=unit_area
        )
        return surface_area
    except Exception as e:
        return f"There was an error calculating the surface area of the file: {e}"


@mcp.tool()
async def calculate_volume(input_file: str, unit_volume: str) -> float | str:
    """Calculate the volume of a 3d object represented by the input file.

    Args:
        input_file (str): The path of the file to get the volume from. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_volume (str): The unit of volume to return the result in. One of 'cm3', 'ft3', 'in3', 'm3', 'yd3', 'usfloz', 'usgal', 'l', 'ml'.

    Returns:
        str: The volume of the file in the specified unit of volume, or an error message if the operation fails.
    """

    logger.info("calculate_volume called for file: %s", input_file)

    try:
        volume = await zoo_calculate_volume(file_path=input_file, unit_vol=unit_volume)
        return volume
    except Exception as e:
        return f"There was an error calculating the volume of the file: {e}"


@mcp.tool()
async def convert_cad_file(
    input_path: str,
    export_path: str | None,
    export_format: str | None,
) -> str:
    """Convert a CAD file from one format to another CAD file format.

    Args:
        input_path (str): The input cad file to convert. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        export_path (str | None): The path to save the converted CAD file to. If the path is a directory, a temporary file will be created in the directory. If the path is a file, it will be overwritten if the extension is valid.
        export_format (str): The format of the exported CAD file. This should be one of 'fbx', 'glb', 'gltf', 'obj', 'ply', 'step', 'stl'. If no format is provided, the default is 'step'.

    Returns:
        str: The path to the converted CAD file, or an error message if the operation fails.
    """

    logger.info("convert_cad_file called")

    try:
        step_path = await zoo_convert_cad_file(
            input_path=input_path, export_path=export_path, export_format=export_format
        )
        return str(step_path)
    except Exception as e:
        return f"There was an error converting the CAD file: {e}"


@mcp.tool()
async def export_kcl(
    kcl_code: str | None,
    kcl_path: str | None,
    export_path: str | None,
    export_format: str,
) -> str:
    """Export KCL code to a CAD file. Either kcl_code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file or a directory containing a main.kcl file.

    Args:
        kcl_code (str): The KCL code to export to a CAD file.
        kcl_path (str | None): The path to a KCL file to export to a CAD file. The path should point to a .kcl file or a directory containing a main.kcl file.
        export_path (str | None): The path to export the CAD file. If no path is provided, a temporary file will be created.
        export_format (str): The format to export the file as. This should be one of 'fbx', 'glb', 'gltf', 'obj', 'ply', 'step', 'stl'. If no format is provided, the default is 'step'.

    Returns:
        str: The path to the converted CAD file, or an error message if the operation fails.
    """

    logger.info("convert_kcl_to_step called")

    try:
        cad_path = await zoo_export_kcl(
            kcl_code=kcl_code,
            kcl_path=kcl_path,
            export_path=export_path,
            export_format=export_format,
        )
        return str(cad_path)
    except Exception as e:
        return f"There was an error exporting the CAD file: {e}"


@mcp.tool()
async def multiview_snapshot_of_cad(
    input_file: str,
    padding: float = 0.2,
) -> ImageContent | str:
    """Save a multiview snapshot of a CAD file. The input file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl

    This multiview image shows the render of the model from 4 different views:
        The top left images is a front view.
        The top right image is a right side view.
        The bottom left image is a top view.
        The bottom right image is an isometric view

    Args:
        input_file (str): The path of the file to get the mass from. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        padding (float): The amount of padding to add around the model in the image. Default is 0.2.

    Returns:
        Image: The multiview snapshot of the CAD file as an image, or an error message if the operation fails.
    """

    logger.info("multiview_snapshot_of_cad called for file: %s", input_file)

    try:
        image = zoo_multiview_snapshot_of_cad(
            input_path=input_file,
            padding=padding,
        )
        return encode_image(image)
    except Exception as e:
        return f"There was an error creating the multiview snapshot: {e}"


@mcp.tool()
async def multiview_snapshot_of_kcl(
    kcl_code: str | None,
    kcl_path: str | None,
    padding: float = 0.2,
) -> ImageContent | str:
    """Save a multiview snapshot of KCL code. Either kcl_code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file or a directory containing a main.kcl file.

    This multiview image shows the render of the model from 4 different views:
        The top left images is a front view.
        The top right image is a right side view.
        The bottom left image is a top view.
        The bottom right image is an isometric view

    Args:
        kcl_code (str): The KCL code to export to a CAD file.
        kcl_path (str | None): The path to a KCL file to export to a CAD file. The path should point to a .kcl file or a directory containing a main.kcl file.
        padding (float): The amount of padding to add around the model in the image. Default is 0.2.

    Returns:
        Image: The multiview snapshot of the KCL code as an image, or an error message if the operation fails.
    """

    logger.info("multiview_snapshot_of_kcl called")

    try:
        image = await zoo_multiview_snapshot_of_kcl(
            kcl_code=kcl_code,
            kcl_path=kcl_path,
            padding=padding,
        )
        return encode_image(image)
    except Exception as e:
        return f"There was an error creating the multiview snapshot: {e}"


@mcp.tool()
async def snapshot_of_cad(
    input_file: str,
    camera: dict | None = None,
    padding: float = 0.2,
) -> ImageContent | str:
    """Save a snapshot of a CAD file.

    Args:
        input_file (str): The path of the file to get the mass from. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        camera (dict | None): The camera to use for the snapshot. If using a dict it should have the following keys,
            "up" (list of 3 floats) defining the up vector of the camera, "vantage" (list of 3 floats), and "center" (list of 3 floats).
            If no camera is provided, a default isometric camera will be used.
            For example camera = {"up": [0, 0, 1], "vantage": [0, -1, 0], "center": [0, 0, 0]} would set the camera to be looking at the origin from the right side (-y direction).
        padding (float): The amount of padding to add around the model in the image. Default is 0.2.

    Returns:
        Image: The snapshot of the CAD file as an image, or an error message if the operation fails.
    """

    logger.info("snapshot_of_cad called for file: %s", input_file)

    try:
        if camera is not None:
            camera = OptionDefaultCameraLookAt(
                up=Point3d(x=camera["up"][0], y=camera["up"][1], z=camera["up"][2]),
                vantage=Point3d(
                    x=camera["vantage"][0],
                    y=-camera["vantage"][1],
                    z=camera["vantage"][2],
                ),
                center=Point3d(
                    x=camera["center"][0], y=camera["center"][1], z=camera["center"][2]
                ),
            )

        image = zoo_snapshot_of_cad(
            input_path=input_file,
            camera=camera,
            padding=padding,
        )
        return encode_image(image)
    except Exception as e:
        return f"There was an error creating the snapshot: {e}"


@mcp.tool()
async def snapshot_of_kcl(
    kcl_code: str | None,
    kcl_path: str | None,
    camera: dict | None = None,
    padding: float = 0.2,
) -> ImageContent | str:
    """Save a snapshot of KCL

    Args:
        kcl_code (str): The KCL code to export to a CAD file.
        kcl_path (str | None): The path to a KCL file to export to a CAD file. The path should point to a .kcl file or a directory containing a main.kcl file.
        camera (dict | None): The camera to use for the snapshot. If using a dict it should have the following keys,
            "up" (list of 3 floats) defining the up vector of the camera, "vantage" (list of 3 floats), and "center" (list of 3 floats).
            If no camera is provided, a default isometric camera will be used.
            For example camera = {"up": [0, 0, 1], "vantage": [0, -1, 0], "center": [0, 0, 0]} would set the camera to be looking at the origin from the right side (-y direction).
        padding (float): The amount of padding to add around the model in the image. Default is 0.2.

    Returns:
        Image: The snapshot of the CAD file as an image, or an error message if the operation fails.
    """

    logger.info("snapshot_of_kcl called for file")

    try:
        if camera is not None:
            camera = kcl.CameraLookAt(
                up=kcl.Point3d(x=camera["up"][0], y=camera["up"][1], z=camera["up"][2]),
                vantage=kcl.Point3d(
                    x=camera["vantage"][0],
                    y=-camera["vantage"][1],
                    z=camera["vantage"][2],
                ),
                center=kcl.Point3d(
                    x=camera["center"][0], y=camera["center"][1], z=camera["center"][2]
                ),
            )

        image = await zoo_snapshot_of_kcl(
            kcl_code=kcl_code,
            kcl_path=kcl_path,
            camera=camera,
            padding=padding,
        )
        return encode_image(image)
    except Exception as e:
        return f"There was an error creating the snapshot: {e}"


@mcp.tool()
async def text_to_cad(prompt: str) -> str:
    """Generate a CAD model as KCL code from a text prompt.

    # General Tips
    - You can use verbs like "design a..." or "create a...", but those aren't needed. Prompting "A gear" works as well as "Create a gear".
    - If your prompt omits important dimensions, Text-to-CAD will make its best guess to fill in missing details.
    - Traditional, simple mechanical parts such as fasteners, bearings and connectors work best right now.
    - Text-to-CAD returns a 422 error code if it fails to generate a valid geometry internally, even if it understands your prompt. We're working on reducing the amount of errors.
    - Shorter prompts, 1-2 sentences in length, succeed more often than longer prompts.
    - The maximum prompt length is approximately 6000 words. Generally, shorter prompts of one or two sentences work best. Longer prompts take longer to resolve.
    - The same prompt can generate different results when submitted multiple times. Sometimes a failing prompt will succeed on the next attempt, and vice versa.

    # Examples
    - "A 21-tooth involute helical gear."
    - "A plate with a hole in each corner for a #10 bolt. The plate is 4" wide, 6" tall."
    - "A dodecahedron."
    - "A camshaft."
    - "A 1/2 inch gear with 21 teeth."
    - "A 3x6 lego."

    Args:
        prompt (str): The text prompt to be realized as KCL code.

    Returns:
        str: The generated KCL code if Text-to-CAD is successful, otherwise the error message.
    """
    logger.info("Text-To-CAD called with prompt: %s", prompt)
    try:
        return await _text_to_cad(prompt=prompt)
    except Exception as e:
        return f"There was an error generating the CAD file from text: {e}"


if __name__ == "__main__":
    logger.info("Starting MCP server...")
    mcp.run(transport="stdio")
