import asyncio
from pathlib import Path

import aiofiles
from kittycad import KittyCAD
from kittycad.models import (
    ApiCallStatus,
    FileExportFormat,
    TextToCadCreateBody,
    TextToCadIterationBody,
)
from kittycad.models.text_to_cad_response import (
    OptionTextToCad,
    OptionTextToCadIteration,
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
