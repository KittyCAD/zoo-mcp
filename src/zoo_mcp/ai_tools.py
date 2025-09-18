import asyncio
import os
from pathlib import Path

import aiofiles
from kittycad import KittyCAD
from kittycad.models import (
    ApiCallStatus,
    FileExportFormat,
    TextToCadCreateBody,
    TextToCadIterationBody,
    TextToCadMultiFileIterationBody,
)
from kittycad.models.text_to_cad_response import (
    OptionTextToCad,
    OptionTextToCadIteration,
    OptionTextToCadMultiFileIteration,
)

from zoo_mcp import ZooMCPException, logger

kittycad_client = KittyCAD()


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
    result = kittycad_client.ml.get_text_to_cad_model_for_user(id=t2c.id)

    # check if the request has either completed or failed, otherwise sleep and try again
    while result.root.status not in [ApiCallStatus.COMPLETED, ApiCallStatus.FAILED]:
        result = kittycad_client.ml.get_text_to_cad_model_for_user(id=t2c.id)
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


async def text_to_cad_iteration(
    prompt: str,
    kcl_code: str | None = None,
    kcl_path: Path | str | None = None,
) -> str:
    """Send a prompt to Zoo's Text-To-CAD iteration endpoint. Either kcl_code or kcl_path must be provided. If kcl_path is provided, it should point to a .kcl file

    Args:
        prompt (str): a description of the changes to be made to the CAD model
        kcl_code (str | None): The existing KCL code to be modified
        kcl_path (Path | str | None): KCL path, the path should point to a .kcl file

    Returns:
        A string containing the complete KCL code of the CAD model if Text-To-CAD iteration was successful, otherwise an error
        message from Text-To-CAD
    """

    logger.info("Sending KCL code prompt to Text-To-CAD iteration")

    # default to using the code if both are provided
    if kcl_code and kcl_path:
        logger.warning("Both code and kcl_path provided, using code")
        kcl_path = None

    if kcl_path:
        kcl_path = Path(kcl_path)
        if kcl_path.is_file() and kcl_path.suffix != ".kcl":
            logger.error("The provided kcl_path is not a .kcl file")
            raise ZooMCPException("The provided kcl_path is not a .kcl file")
        if kcl_path.is_dir():
            logger.error("The provided kcl_path is a directory not a .kcl file")
            raise ZooMCPException(
                "The provided kcl_path is a directory not a .kcl file"
            )

    if not kcl_code and not kcl_path:
        logger.error("Neither code nor kcl_path provided")
        raise ZooMCPException("Neither code nor kcl_path provided")

    if kcl_path:
        async with aiofiles.open(kcl_path, "r") as inp:
            kcl_code = await inp.read()

    if not isinstance(kcl_code, str):
        logger.error("kcl_code is not a string")
        raise ZooMCPException("kcl_code is not a string")

    t2ci = kittycad_client.ml.create_text_to_cad_iteration(
        body=TextToCadIterationBody(
            original_source_code=kcl_code, prompt=prompt, source_ranges=[]
        )
    )

    # get the response based on the request id
    result = kittycad_client.ml.get_text_to_cad_model_for_user(id=t2ci.id)

    # check if the request has either completed or failed, otherwise sleep and try again
    while result.root.status not in [ApiCallStatus.COMPLETED, ApiCallStatus.FAILED]:
        result = kittycad_client.ml.get_text_to_cad_model_for_user(id=t2ci.id)
        await asyncio.sleep(1)

    # get the data object (root) of the response
    response = result.root

    # check the data type of the response
    if not isinstance(response, OptionTextToCadIteration):
        return "Error: Text-to-CAD response is not of type OptionTextToCadIteration."

    # if Text To CAD iteration was successful return the KCL code, otherwise return the error
    if response.status == ApiCallStatus.COMPLETED:
        if response.code is None:
            return "Error: Text-to-CAD iteration response is null."
        return response.code
    else:
        if response.error is None:
            return "Error: Text-to-CAD iteration response is null."
        return response.error


async def text_to_cad_multi_file_iteration(
    prompt: str,
    file_paths: list[str] | list[Path] | None = None,
    proj_path: Path | str | None = None,
) -> dict | str:
    """Send a prompt and multiple KCL files to Zoo's Text-To-CAD multi-file iteration endpoint. Either file_paths or proj_path must be provided. If proj_path is provided all contained files will be sent to the endpoint.

    Args:
        prompt (str): a description of the changes to be made to the CAD model associated with the provided KCL files
        file_paths (list[Path | str] | None): A list of paths to KCL files
        proj_path (Path | str | None): A path to a directory containing a main.kcl file. All contained files will be sent to the endpoint.

    Returns:
        dict | str: A dictionary containing the complete KCL code of the CAD model if Text-To-CAD multi-file iteration was successful.
                    Each key in the dict, refers to a kcl file path relative to the project path (determined by the commonpath if a project path is not supplied), and the value is the complete KCL code for that file.
                    otherwise an error message from Text-To-CAD
    """
    logger.info("Sending KCL code prompt to Text-To-CAD multi file iteration")

    # default to using the project if both are provided
    if file_paths and proj_path:
        logger.warning("Both file paths and project path provided, using project path")
        file_paths = None

    if file_paths:
        file_paths = [Path(fp) for fp in file_paths]
        # find the common path of all file paths to use as the project path
        path_strings = [str(p.resolve()) for p in file_paths]
        common_path = os.path.commonpath(path_strings)
        proj_path = Path(common_path)
    else:
        logger.info("Finding all files in project path")
        proj_path = Path(proj_path)
        file_paths = list(proj_path.rglob("*"))

    if not file_paths:
        logger.error("No files paths provided or found in project path")
        raise ZooMCPException("No file paths provided or found in project path")

    if ".kcl" not in [fp.suffix for fp in file_paths]:
        logger.error("No .kcl extension found in provided file paths")
        raise ZooMCPException("No .kcl extension found in provided file paths")

    file_attachments = {
        str(fp.relative_to(proj_path)): fp for fp in file_paths if fp.is_file()
    }

    t2cmfi = kittycad_client.ml.create_text_to_cad_multi_file_iteration(
        body=TextToCadMultiFileIterationBody(
            source_ranges=[],
            prompt=prompt,
        ),
        file_attachments=file_attachments,
    )

    # get the response based on the request id
    result = kittycad_client.ml.get_text_to_cad_model_for_user(id=t2cmfi.id)

    # check if the request has either completed or failed, otherwise sleep and try again
    while result.root.status not in [ApiCallStatus.COMPLETED, ApiCallStatus.FAILED]:
        result = kittycad_client.ml.get_text_to_cad_model_for_user(id=t2cmfi.id)
        await asyncio.sleep(1)

    # get the data object (root) of the response
    response = result.root

    # check the data type of the response
    if not isinstance(response, OptionTextToCadMultiFileIteration):
        return "Error: Text-to-CAD response is not of type OptionTextToCadMultiFileIteration."

    # if Text To CAD iteration was successful return the KCL code, otherwise return the error
    if response.status == ApiCallStatus.COMPLETED:
        if response.outputs is None:
            return "Error: Text-to-CAD iteration response is null."
        return response.outputs
    else:
        if response.error is None:
            return "Error: Text-to-CAD iteration response is null."
        return response.error
