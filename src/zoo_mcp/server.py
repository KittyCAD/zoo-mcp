from mcp.server.fastmcp import FastMCP, Image

from zoo_mcp import logger
from zoo_mcp.ai_tools import _text_to_cad
from zoo_mcp.zoo_tools import (
    zoo_export_kcl,
    zoo_convert_cad_file,
    zoo_calculate_center_of_mass,
    zoo_calculate_mass,
    zoo_calculate_surface_area,
    zoo_calculate_volume,
    zoo_multiview_snapshot_of_kcl,
)

mcp = FastMCP(
    name="Zoo MCP Server",
)


@mcp.tool()
async def calculate_center_of_mass(input_file: str, unit_length: str) -> str:
    """Calculate the center of mass of a 3d object represented by the input file.

    Args:
        input_file (str): The path of the file to get the mass from. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_length (str): The unit of length to return the result in. One of 'cm', 'ft', 'in', 'm', 'mm', 'yd'

    Returns:
        str: The center of mass of the file in the specified unit of length, or an error message if the operation fails.
    """

    logger.info("calculate_center_of_mass called for file: %s", input_file)

    com = await zoo_calculate_center_of_mass(file_path=input_file, unit_length=unit_length)
    if com:
        return f"The center of mass of the file is {com} with units of length of {unit_length}."
    else:
        return "The center of mass of the file could not be determined."


@mcp.tool()
async def calculate_mass(
    input_file: str, unit_mass: str, unit_density: str, density: float
) -> str:
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

    mass = await zoo_calculate_mass(
        file_path=input_file, unit_mass=unit_mass, unit_density=unit_density, density=density
    )
    if mass:
        return f"The mass of the file is {mass} {unit_mass}."
    else:
        return "The mass of the file could not be determined."


@mcp.tool()
async def calculate_surface_area(input_file: str, unit_area: str) -> str:
    """Calculate the surface area of a 3d object represented by the input file.

    Args:
        input_file (str): The path of the file to get the surface area from. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_area (str): The unit of area to return the result in. One of 'cm2', 'dm2', 'ft2', 'in2', 'km2', 'm2', 'mm2', 'yd2'.

    Returns:
        str: The surface area of the file in the specified unit of area, or an error message if the operation fails.
    """

    logger.info("calculate_surface_area called for file: %s", input_file)

    surface_area = await zoo_calculate_surface_area(
        file_path=input_file, unit_area=unit_area
    )
    if surface_area:
        return f"The surface area of the file is {surface_area} {unit_area}."
    else:
        return "The surface area of the file could not be determined."


@mcp.tool()
async def calculate_volume(input_file: str, unit_volume: str) -> str:
    """Calculate the volume of a 3d object represented by the input file.

    Args:
        input_file (str): The path of the file to get the volume from. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_volume (str): The unit of volume to return the result in. One of 'cm3', 'ft3', 'in3', 'm3', 'yd3', 'usfloz', 'usgal', 'l', 'ml'.

    Returns:
        str: The volume of the file in the specified unit of volume, or an error message if the operation fails.
    """

    logger.info("calculate_volume called for file: %s", input_file)

    volume = await zoo_calculate_volume(file_path=input_file, unit_vol=unit_volume)
    if volume:
        return f"The volume of the file is {volume} {unit_volume}."
    else:
        return "The volume of the file could not be determined."


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

    step_path = await zoo_convert_cad_file(
        input_path=input_path, export_path=export_path, export_format=export_format
    )
    if step_path:
        return f"The file was successfully converted to a CAD file at: {step_path}"
    else:
        return "The file could not be converted to a CAD file."


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

    cad_path = await zoo_export_kcl(
        kcl_code=kcl_code,
        kcl_path=kcl_path,
        export_path=export_path,
        export_format=export_format,
    )
    if cad_path:
        return f"The KCL code was successfully exported to a CAD file at: {cad_path}"
    return "The KCL code could not be exported to a CAD file."


@mcp.tool()
async def multiview_snapshot_of_kcl(
    kcl_code: str | None,
    kcl_path: str | None,
    padding: float = 0.2,
) -> Image | str:
    """Save a multiview snapshot of KCL code. Each quadrant of the image. Either kcl_code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file or a directory containing a main.kcl file.

    This multiview image shows the render of the model from 4 different views:
        The top left images is a front view.
        The top right image is a right side view.
        The bottom left image is a top view.
        The bottom right image is an isometric view

    Args:
        kcl_code (str): The KCL code to export to a CAD file.
        kcl_path (str | None): The path to a KCL file to export to a CAD file. The path should point to a .kcl file or a directory containing a main.kcl file.
        padding:

    Returns:
        Image: The multiview snapshot of the KCL code as an image, or an error message if the operation fails.
    """

    logger.info("multiview_snapshot_of_kcl called")

    image = await zoo_multiview_snapshot_of_kcl(
        kcl_code=kcl_code,
        kcl_path=kcl_path,
        padding=padding,
    )
    if image:
        return image
    return "The multiview snapshot could not be created."


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
    return await _text_to_cad(prompt=prompt)


if __name__ == "__main__":
    logger.info("Starting MCP server...")
    mcp.run(transport="stdio")
