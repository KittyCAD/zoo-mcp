import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError

from zoo_mcp import logger
from zoo_mcp.ai_tools import _text_to_cad
from zoo_mcp.zoo_tools import (
    _zoo_export_kcl,
    _zoo_convert_cad_file,
    _zoo_calculate_center_of_mass,
    _zoo_calculate_mass,
    _zoo_calculate_surface_area,
    _zoo_calculate_volume,
)

mcp = FastMCP(
    name="Zoo MCP Server",
)


def _verify_file_scheme(path: types.FileUrl | None) -> str | None:
    # first verify the path is a file:// URI otherwise raise an MCP error
    if path is None:
        return None

    if path.scheme != "file":
        raise McpError(
            types.ErrorData(
                code=types.INVALID_PARAMS,
                message="Invalid URI scheme - only file:// URIs are supported",
            )
        )
    # format the path to remove the file:// scheme, downstream tools expect a local filesystem path
    new_path = str(path).replace("file://", "")
    return new_path


@mcp.tool()
async def calculate_center_of_mass(path: types.FileUrl, unit_length: str) -> str:
    """Get the center of mass of a file.

    Args:
        path (types.FileUrl): The path of the file to get the mass from. This should be available on the local filesystem and be a file:// URI. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_length (str): The unit of length to return the result in. One of 'cm', 'ft', 'in', 'm', 'mm', 'yd'

    Returns:
        str: The center of mass of the file in the specified unit of length, or an error message if the operation fails.
    """
    path = _verify_file_scheme(path)

    logger.info("Received calculate_center_of_mass request for file: %s", path)

    success, com = await _zoo_calculate_center_of_mass(
        file_path=path, unit_length=unit_length
    )
    if success:
        return f"The center of mass of the file is {com} with units of length of {unit_length}."
    else:
        return "The center of mass of the file could not be determined."


@mcp.tool()
async def calculate_mass(
    path: types.FileUrl, unit_mass: str, unit_density: str, density: float
) -> str:
    """Get the mass of a file.

    Args:
        path (types.FileUrl): The path of the file to get the mass from. This should be available on the local filesystem and be a file:// URI. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_mass (str): The unit of mass to return the result in. One of 'g', 'kg', 'lb'.
        unit_density (str): The unit of density to calculate the mass. One of 'lb:ft3', 'kg:m3'.
        density (float): The density of the material.

    Returns:
        str: The mass of the file in the specified unit of mass, or an error message if the operation fails.
    """
    path: str = _verify_file_scheme(path)

    logger.info("Received calculate_mass request for file: %s", path)

    success, mass = await _zoo_calculate_mass(
        file_path=path, unit_mass=unit_mass, unit_density=unit_density, density=density
    )
    if success:
        return f"The mass of the file is {mass} {unit_mass}."
    else:
        return "The mass of the file could not be determined."


@mcp.tool()
async def calculate_surface_area(path: types.FileUrl, unit_area: str) -> str:
    """Get the surface area of a file.

    Args:
        path (types.FileUrl): The path of the file to get the surface area from. This should be available on the local filesystem and be a file:// URI. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_area (str): The unit of area to return the result in. One of 'cm2', 'dm2', 'ft2', 'in2', 'km2', 'm2', 'mm2', 'yd2'.

    Returns:
        str: The surface area of the file in the specified unit of area, or an error message if the operation fails.
    """
    path: str = _verify_file_scheme(path)

    logger.info("Received calculate_surface_area request for file: %s", path)

    success, surface_area = await _zoo_calculate_surface_area(
        file_path=path, unit_area=unit_area
    )
    if success:
        return f"The surface area of the file is {surface_area} {unit_area}."
    else:
        return "The surface area of the file could not be determined."


@mcp.tool()
async def calculate_volume(path: types.FileUrl, unit_volume: str) -> str:
    """Get the volume of a file.

    Args:
        path (types.FileUrl): The path of the file to get the volume from. This should be available on the local filesystem and be a file:// URI. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        unit_volume (str): The unit of volume to return the result in. One of 'cm3', 'ft3', 'in3', 'm3', 'yd3', 'usfloz', 'usgal', 'l', 'ml'.

    Returns:
        str: The volume of the file in the specified unit of volume, or an error message if the operation fails.
    """
    path: str = _verify_file_scheme(path)

    logger.info("Received calculate_volume request for file: %s", path)

    success, volume = await _zoo_calculate_volume(file_path=path, unit_vol=unit_volume)
    if success:
        return f"The volume of the file is {volume} {unit_volume}."
    else:
        return "The volume of the file could not be determined."


@mcp.tool()
async def convert_cad_file(
    input_path: types.FileUrl,
    export_path: types.FileUrl | None,
    export_format: str | None,
) -> str:
    """Convert a CAD file from one format to another CAD file format.

    Args:
        input_path (types.FileUrl): The input cad file to convert. This should be available on the local filesystem and be a file:// URI. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stl
        export_path (types.FileUrl | None): The path to save the converted CAD file to. This should be a file:// URI. If no path is provided, a temporary file will be created. If the path is a directory, a temporary file will be created in the directory. If the path is a file, it will be overwritten if the extension is valid.
        export_format (str): The format of the exported CAD file. This should be one of 'fbx', 'glb', 'gltf', 'obj', 'ply', 'step', 'stl'. If no format is provided, the default is 'step'.

    Returns:
        str: The path to the converted CAD file, or an error message if the operation fails.
    """

    logger.info("Received convert_cad_file request.")

    project_path: str = _verify_file_scheme(input_path)
    export_path: str = _verify_file_scheme(export_path)

    success, step_path = await _zoo_convert_cad_file(
        input_path=project_path, export_path=export_path, export_format=export_format
    )
    if success:
        return (
            f"The file was successfully converted to a CAD file at: file://{step_path}"
        )
    else:
        return "The file could not be converted to a CAD file."


@mcp.tool()
async def export_kcl(
    kcl_code: str | None,
    kcl_path: types.FileUrl | None,
    export_path: types.FileUrl | None,
    export_format: str,
) -> str:
    """Export KCL code to a CAD file. Either kcl_code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file or a directory containing a main.kcl file.

    Args:
        kcl_code (str): The KCL code to export to a CAD file.
        kcl_path (types.FileUrl | None): The path to a KCL file to export to a CAD file. This should be available on the local filesystem and be a file:// URI. The path should point to a .kcl file or a directory containing a main.kcl file.
        export_path (types.FileUrl | None): The path to export the CAD file. This must be a file:// URI to a local filesystem path with the .step extension. If no path is provided, a temporary file will be created.
        export_format (str): The format to export the file as. This should be one of 'fbx', 'glb', 'gltf', 'obj', 'ply', 'step', 'stl'. If no format is provided, the default is 'step'.

    Returns:
        str: The path to the converted CAD file, or an error message if the operation fails.
    """

    logger.info("Received convert_kcl_to_step request.")

    export_path: str = _verify_file_scheme(export_path)

    success, step_path = await _zoo_export_kcl(
        kcl_code=kcl_code,
        kcl_path=kcl_path,
        export_path=export_path,
        export_format=export_format,
    )
    if success:
        return f"The KCL code was successfully exported to a CAD file at: file://{step_path}"
    return "The KCL code could not be exported to a CAD file."


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
    logger.info("Received Text-To-CAD prompt: %s", prompt)
    return await _text_to_cad(prompt=prompt)


if __name__ == "__main__":
    logger.info("Starting MCP server...")
    mcp.run(transport="stdio")
