import asyncio
from pathlib import Path

from kittycad.models import (
    ApiCallStatus,
    FileExportFormat,
    TextToCadCreateBody,
    TextToCadMultiFileIterationBody,
)
from kittycad.models.text_to_cad_response import (
    OptionTextToCad,
    OptionTextToCadMultiFileIteration,
)

from zoo_mcp import ZooMCPException, kittycad_client, logger


async def text_to_cad(prompt: str) -> str:
    """Send a prompt to Zoo's Text-To-CAD create endpoint

    Args:
        prompt (str): a description of the CAD model to be created

    Returns:
        A string containing the complete KCL code of the CAD model if Text-To-CAD was successful, otherwise an error
        message from Text-To-CAD
    """

    logger.info("Sending prompt to Text-To-CAD")

    # send prompt via the kittycad client
    t2c = kittycad_client.ml.create_text_to_cad(
        output_format=FileExportFormat.STEP,
        kcl=True,
        body=TextToCadCreateBody(
            prompt=prompt,
        ),
    )

    # get the response based on the request id
    result = kittycad_client.ml.get_text_to_cad_parts_for_user(id=t2c.id)

    # check if the request has either completed or failed, otherwise sleep and try again
    while result.root.status not in [ApiCallStatus.COMPLETED, ApiCallStatus.FAILED]:
        result = kittycad_client.ml.get_text_to_cad_parts_for_user(id=t2c.id)
        await asyncio.sleep(1)

    logger.info("Received response from Text-To-CAD")

    # get the data object (root) of the response
    response = result.root

    # check the data type of the response
    if not isinstance(response, OptionTextToCad):
        return "Error: Text-to-CAD response is not of type OptionTextToCad."

    # if Text To CAD was successful return the KCL code, otherwise return the error
    if response.status == ApiCallStatus.COMPLETED:
        if response.code is None:
            return "Error: Text-to-CAD response is null."
        return response.code
    else:
        if response.error is None:
            return "Error: Text-to-CAD response is null."
        return response.error


async def edit_kcl_project(
    prompt: str,
    proj_path: Path | str,
) -> dict | str:
    """Send a prompt and a KCL project to Zoo's Text-To-CAD edit KCL project endpoint. The proj_path will upload all contained files to the endpoint. There must be a main.kcl file in the root of the project.

    Args:
        prompt (str): A description of the changes to be made to the KCL project associated with the provided KCL files.
        proj_path (Path | str): A path to a directory containing a main.kcl file. All contained files (found recursively) will be sent to the endpoint.

    Returns:
        dict | str: A dictionary containing the complete KCL code of the CAD model if Text-To-CAD edit KCL project was successful.
                    Each key in the dict refers to a KCL file path relative to the project path, and each value is the complete KCL code for that file.
                    If unsuccessful, returns an error message from Text-To-CAD.
    """
    logger.info("Sending KCL code prompt to Text-To-CAD edit kcl project")

    logger.info("Finding all files in project path")
    proj_path = Path(proj_path)
    file_paths = list(proj_path.rglob("*"))
    file_paths = [fp for fp in file_paths if fp.is_file()]
    logger.info("Found %s files in project path", len(file_paths))

    if not file_paths:
        logger.error("No files paths provided or found in project path")
        raise ZooMCPException("No file paths provided or found in project path")

    if ".kcl" not in [fp.suffix for fp in file_paths]:
        logger.error("No .kcl files found in the provided project path")
        raise ZooMCPException("No .kcl files found in the provided project path")

    if not (proj_path / "main.kcl").is_file():
        logger.error("No main.kcl file found in the root of the provided project path")
        raise ZooMCPException(
            "No main.kcl file found in the root of the provided project path"
        )

    file_attachments = {
        str(fp.relative_to(proj_path)): str(fp.resolve()) for fp in file_paths
    }

    t2cmfi = kittycad_client.ml.create_text_to_cad_multi_file_iteration(
        body=TextToCadMultiFileIterationBody(
            source_ranges=[],
            prompt=prompt,
        ),
        file_attachments=file_attachments,
    )

    # get the response based on the request id
    result = kittycad_client.ml.get_text_to_cad_parts_for_user(id=t2cmfi.id)

    # check if the request has either completed or failed, otherwise sleep and try again
    while result.root.status not in [ApiCallStatus.COMPLETED, ApiCallStatus.FAILED]:
        result = kittycad_client.ml.get_text_to_cad_parts_for_user(id=t2cmfi.id)
        await asyncio.sleep(1)

    # get the data object (root) of the response
    response = result.root

    # check the data type of the response
    if not isinstance(response, OptionTextToCadMultiFileIteration):
        return "Error: Text-to-CAD response is not of type OptionTextToCadMultiFileIteration."

    # if Text To CAD iteration was successful return the KCL code, otherwise return the error
    if response.status == ApiCallStatus.COMPLETED:
        if response.outputs is None:
            return "Error: Text-to-CAD edit kcl project response is null."
        return response.outputs
    else:
        if response.error is None:
            return "Error: Text-to-CAD edit kcl project response is null."
        return response.error
