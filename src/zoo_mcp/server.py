import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError

from zoo_mcp import logger
from zoo_mcp.ai_tools import _text_to_cad
from zoo_mcp.zoo_tools import (
    _zoo_convert_code_to_step,
    _zoo_convert_file_to_step,
    _zoo_get_mass,
    _zoo_get_surface_area,
    _zoo_get_volume,
)

mcp = FastMCP(
    name="Zoo MCP Server",
)


def _verify_file_scheme(path: types.AnyUrl) -> str:
    # first verify the path is a file:// URI otherwise raise an MCP error
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
async def convert_kcl_to_step(kcl_code: str, output_path: types.AnyUrl) -> str:
    """Export KCL code to a STEP file.

    Args:
        kcl_code (str): The KCL code to export to a STEP file.
        output_path (AnyUrl | None): The path to export the STEP file. This must be a file:// URI to a local filesystem path with the .step extension. If no path is provided, a temporary file will be created.

    Returns:
        str: The path to the converted STEP file, or an error message if the operation fails.
    """

    logger.info("Received convert_kcl_to_step request.")

    output_path: str = _verify_file_scheme(output_path)

    success, step_path = await _zoo_convert_code_to_step(
        code=kcl_code, export_path=output_path
    )
    if success:
        return f"The KCL code was successfully converted to a STEP file at: file://{step_path}"
    return "The KCL code could not be converted to a STEP file."


@mcp.tool()
async def convert_file_to_step(path: types.AnyUrl, output_path: types.AnyUrl) -> str:
    """Convert a file or directory to a STEP file. If converting a file, the file should be written in kcl and have the .kcl extension. If converting a directory, the directory should contain a KCL project with a main.kcl file.

    Args:
        path (uri): The path to convert to a step. This should be available on the local filesystem and be a file:// URI. The path can be to a single .kcl file or to a directory containing a KCL project with a main.kcl file.
        output_path (uri | None): The path to save the converted STEP file to. This should be a file:// URI. to a local filesystem path with the .step extension. If no path is provided, a temporary file will be created.

    Returns:
        str: The path to the converted STEP file, or an error message if the operation fails.
    """

    logger.info("Received convert_kcl_to_step request.")

    project_path: str = _verify_file_scheme(path)
    output_path: str = _verify_file_scheme(output_path)

    success, step_path = await _zoo_convert_file_to_step(
        proj_path=project_path, export_path=output_path
    )
    if success:
        return (
            f"The file was successfully converted to a STEP file at: file://{step_path}"
        )
    else:
        return "The file could not be converted to a STEP file."


@mcp.tool()
async def get_file_mass(
    path: types.AnyUrl, unit_mass: str, unit_density: str, density: float
) -> str:
    """Get the mass of a file.

    Args:
        path (uri): The path of the file to get the mass from. This should be available on the local filesystem and be a file:// URI. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stp, .stl
        unit_mass (str): The unit of mass to return the result in. One of 'g', 'kg', 'lb'.
        unit_density (str): The unit of density to calculate the mass. One of 'lb:ft3', 'kg:m3'.
        density (float): The density of the material.

    Returns:
        str: The mass of the file in the specified unit of mass, or an error message if the operation fails.
    """
    path: str = _verify_file_scheme(path)

    logger.info("Received get_file_mass request for file: %s", path)

    success, mass = await _zoo_get_mass(
        file_path=path, unit_mass=unit_mass, unit_density=unit_density, density=density
    )
    if success:
        return f"The mass of the file is {mass} {unit_mass}."
    else:
        return "The mass of the file could not be determined."


@mcp.tool()
async def get_file_surface_area(path: types.AnyUrl, unit_area: str) -> str:
    """Get the surface area of a file.

    Args:
        path (uri): The path of the file to get the surface area from. This should be available on the local filesystem and be a file:// URI. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stp, .stl
        unit_area (str): The unit of area to return the result in. One of 'cm2', 'dm2', 'ft2', 'in2', 'km2', 'm2', 'mm2', 'yd2'.

    Returns:
        str: The surface area of the file in the specified unit of area, or an error message if the operation fails.
    """
    path: str = _verify_file_scheme(path)

    logger.info("Received get_file_surface_area request for file: %s", path)

    success, surface_area = await _zoo_get_surface_area(
        file_path=path, unit_area=unit_area
    )
    if success:
        return f"The surface area of the file is {surface_area} {unit_area}."
    else:
        return "The surface area of the file could not be determined."


@mcp.tool()
async def get_file_volume(path: types.AnyUrl, unit_volume: str) -> str:
    """Get the volume of a file.

    Args:
        path (uri): The path of the file to get the volume from. This should be available on the local filesystem and be a file:// URI. The file should be one of the supported formats: .fbx, .gltf, .obj, .ply, .sldprt, .step, .stp, .stl
        unit_volume (str): The unit of volume to return the result in. One of 'cm3', 'ft3', 'in3', 'm3', 'yd3', 'usfloz', 'usgal', 'l', 'ml'.

    Returns:
        str: The volume of the file in the specified unit of volume, or an error message if the operation fails.
    """
    path: str = _verify_file_scheme(path)

    logger.info("Received get_file_volume request for file: %s", path)

    success, volume = await _zoo_get_volume(file_path=path, unit_vol=unit_volume)
    if success:
        return f"The volume of the file is {volume} {unit_volume}."
    else:
        return "The volume of the file could not be determined."


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
