import asyncio

from kittycad import KittyCAD
from kittycad.models import (
    ApiCallStatus,
    FileExportFormat,
    TextToCadCreateBody,
)
from kittycad.models.text_to_cad_response import OptionTextToCad

kittycad_client = KittyCAD()


async def text_to_cad(prompt: str) -> str:
    """Send a prompt to Zoo's Text-To-CAD create endpoint

    Args:
        prompt (str): a description of the CAD model to be created

    Returns:
        A string containing the complete KCL code of the CAD model if Text-To-CAD was successful, otherwise an error
        message from Text-To-CAD
    """
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
