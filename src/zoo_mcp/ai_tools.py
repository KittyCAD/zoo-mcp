import asyncio
import time
from pathlib import Path

import websockets
from kittycad.models import (
    ApiCallStatus,
    FileExportFormat,
    TextToCadCreateBody,
    TextToCadMultiFileIterationBody,
)
from kittycad.models.ml_copilot_server_message import EndOfStream, Reasoning, ToolOutput
from kittycad.models.reasoning_message import (
    OptionCreatedKclFile,
    OptionDeletedKclFile,
    OptionDesignPlan,
    OptionFeatureTreeOutline,
    OptionGeneratedKclCode,
    OptionKclCodeError,
    OptionKclCodeExamples,
    OptionKclDocs,
    OptionMarkdown,
    OptionText,
    OptionUpdatedKclFile,
)
from kittycad.models.text_to_cad_response import (
    OptionTextToCad,
    OptionTextToCadMultiFileIteration,
)

from zoo_mcp import ZooMCPException, kittycad_client, logger


def log_websocket_message(conn_id: str) -> bool:
    logger.info("Connecting to Text-To-CAD websocket...")
    with kittycad_client.ml.ml_reasoning_ws(id=conn_id) as ws:
        logger.info(
            "Successfully connected to Text-To-CAD websocket with id %s", conn_id
        )
        while True:
            try:
                message = ws.recv()
                if isinstance(message.root, Reasoning):
                    message_option = message.root.reasoning.root
                    match message_option:
                        case OptionCreatedKclFile():
                            logger.info(
                                "Created %s: %s"
                                % (message_option.file_name, message_option.content),
                            )
                        case OptionDeletedKclFile():
                            logger.info("Deleted %s", message_option.file_name)
                        case OptionDesignPlan():
                            design_steps = " ".join(
                                [
                                    f"Editing: {step.filepath_to_edit} with these instruction {step.edit_instructions}"
                                    for step in message_option.steps
                                ]
                            )
                            logger.info("Design Plan: %s", design_steps)
                        case OptionFeatureTreeOutline():
                            logger.info(
                                "Feature Tree Outline: %s", message_option.content
                            )
                        case OptionGeneratedKclCode():
                            logger.info("Generated KCL code: %s", message_option.code)
                        case OptionKclCodeError():
                            logger.info("KCL Code Error: %s", message_option.error)
                        case OptionKclDocs():
                            logger.info("KCL Docs: %s", message_option.content)
                        case OptionKclCodeExamples():
                            logger.info("KCL Code Examples: %s", message_option.content)
                        case OptionMarkdown():
                            logger.info(message_option.content)
                        case OptionText():
                            logger.info(message_option.content)
                        case OptionUpdatedKclFile():
                            logger.info(
                                "Updated %s: %s"
                                % (message_option.file_name, message_option.content),
                            )
                        case _:
                            logger.info(
                                "Received unhandled reasoning message: %s",
                                type(message_option),
                            )
                if isinstance(message.root, ToolOutput):
                    tool_result = message.root.result.root
                    if tool_result.error:
                        logger.info(
                            "Tool: %s, Error: %s"
                            % (tool_result.type, tool_result.error)
                        )
                    else:
                        logger.info(
                            "Tool: %s, Output: %s"
                            % (tool_result.type, tool_result.outputs)
                        )
                if isinstance(message.root, EndOfStream):
                    logger.info("Text-To-CAD reasoning complete.")
                    return True

            except websockets.exceptions.ConnectionClosedError as e:  # ty: ignore[unresolved-attribute]
                logger.info(
                    "Text To CAD could still be running but the websocket connection closed with error: %s",
                    e,
                )
                return False

            except Exception as e:
                logger.info(
                    "Text To CAD could still be running but an unexpected error occurred: %s",
                    e,
                )
                return False


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
    result = kittycad_client.ml.get_text_to_cad_part_for_user(id=t2c.id)

    # check if the request has either completed or failed, otherwise sleep and try again
    time_start = time.time()
    ws_complete = False
    while result.root.status not in [ApiCallStatus.COMPLETED, ApiCallStatus.FAILED]:
        if (
            result.root.status == ApiCallStatus.QUEUED
            and (time.time() - time_start) % 5 == 0
        ):
            logger.info("Text-To-CAD queued...")
        if result.root.status == ApiCallStatus.IN_PROGRESS:
            logger.info("Text-To-CAD in progress...")
            if not ws_complete:
                ws_complete = log_websocket_message(t2c.id)
        logger.info(
            "Waiting for Text-To-CAD to complete... status %s", result.root.status
        )
        result = kittycad_client.ml.get_text_to_cad_part_for_user(id=t2c.id)
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

    log_websocket_message(t2cmfi.id)

    # get the response based on the request id
    result = kittycad_client.ml.get_text_to_cad_part_for_user(id=t2cmfi.id)

    # check if the request has either completed or failed, otherwise sleep and try again
    while result.root.status not in [ApiCallStatus.COMPLETED, ApiCallStatus.FAILED]:
        result = kittycad_client.ml.get_text_to_cad_part_for_user(id=t2cmfi.id)
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
