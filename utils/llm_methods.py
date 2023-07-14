# coding=utf-8
import json
from abc import ABC
import logging

import hyperdb
import numpy
import openai
from hyperdb import hyper_SVM_ranking_algorithm_sort

from utils.basic_llm_calls import openai_chat, get_embeddings
from utils.logging_handler import logging_handlers
from utils.misc import extract_code_blocks
from utils.prompts import REQUEST_IMPROVER
from utils.toolbox import ToolBox

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handlers = logging_handlers()
for each_handler in handlers:
    logger.addHandler(each_handler)


class ExtractionException(Exception):
    pass


class LLMMethods(ABC):
    openai.api_key_path = "resources/openai_api_key.txt"

    @staticmethod
    def improve_request(main_request: str, *parameters: any, **kwargs: any) -> str:
        prompt = REQUEST_IMPROVER.format(request=main_request)
        improved_request = LLMMethods.respond(prompt, list(), *parameters, **kwargs)
        return improved_request.strip()

    @staticmethod
    def vector_summarize(request: str, text: str, segment_size: int = 500, overlap: int = 100, nearest_neighbors: int = 5, **parameters: any) -> str:
        # segment text
        len_text = len(text)
        segments = [text[max(0, i - overlap):min(i + segment_size + overlap, len_text)].strip() for i in range(0, len_text, segment_size)]
        logger.info(f"Summarizing {len(segments)} segments...")

        for i in range(len(segments)):
            if i >= 1:
                segments[i] = "[...]" + segments[i]

            if i < len(segments) - 1:
                segments[i] += "[...]"

        logger.info("Initializing database...")
        db = hyperdb.HyperDB()

        # embed
        logger.info("Embedding...")
        embeddings = get_embeddings([request] + segments)

        request_vector = embeddings[0]
        segment_vectors = embeddings[1:]

        # put embeddings in database
        logger.info("Adding to database...")
        db.add_documents(segments, vectors=segment_vectors)

        # get nearest neighbors
        logger.info("Getting nearest neighbors...")
        nearest_neighbor_indices, _ = hyper_SVM_ranking_algorithm_sort(
            db.vectors,
            numpy.array(request_vector),
            top_k=nearest_neighbors
        )

        nearest_neighbors = [db.documents[i] for i in nearest_neighbor_indices]
        concatenated = "\n\n".join(nearest_neighbors)

        prompt = (f"## Segments\n"
                  f"{concatenated}\n"
                  f"\n"
                  f"## Instruction\n"
                  f"Summarize the text segments above into one concise and coherent paragraph.")

        response = LLMMethods.respond(prompt, list(), function_id="summarize", **parameters)
        return response.strip()

    @staticmethod
    def extract_arguments(text: str, tool_schema: dict[str, any], be_creative: bool = False, **parameters: any) -> dict[str, any]:
        json_schema = json.dumps(tool_schema, indent=2, sort_keys=True)
        if be_creative:
            prompt = (
                f"## Instructions\n"
                f"Create a JSON code block starting with \"```json\" and ending in \"```\" that contains a JSON object in compliance with the schema below. Take "
                f"creative liberties to infer all the required information in the spirit of the provided text. Pay careful attention to the required data types, "
                f"structure, and descriptions.\n"
            )

        else:
            prompt = (
                f"## Instructions\n"
                f"Read the provided text and identify relevant information that fits within the categories specified by the JSON schema below. Use this data to create a "
                f"JSON code block starting with \"```json\" and ending in \"```\" that contains a JSON object in compliance with the schema. Pay careful attention to "
                f"the required data types, structure, and descriptions.\n")

        prompt += (
            f"\n"
            f"## JSON Schema\n"
            f"{json_schema}\n"
            f"\n"
            f"<!-- BEGIN TEXT -->\n"
            f"{text.strip()}\n"
            f"<!-- END TEXT -->")

        response = LLMMethods.respond(prompt, list(), function_id="extract_arguments", **parameters)
        code_block = extract_code_blocks(response)[0]
        arguments = json.loads(code_block)
        return arguments

    @staticmethod
    def openai_extract_arguments(full_description: str, tool_schema: dict[str, any], model="gpt-3.5-turbo-0613", strict: bool = True, **parameters: any) -> dict[str, any]:
        response = openai_chat(
            f"extracting with `{tool_schema['name']}`",
            model=model,
            messages=[{"role": "user", "content": full_description}],
            functions=[tool_schema],
            function_call={"name": tool_schema["name"]},
            **parameters,
        )

        each_choice, = response.choices
        finish_reason = each_choice["finish_reason"]
        if finish_reason != "stop":
            raise ExtractionException(f"OpenAI API did not stop as expected. Finish reason: {finish_reason}")

        response_message = each_choice["message"]
        function_call = response_message["function_call"]
        function_name = function_call["name"]
        if function_name != tool_schema["name"]:
            raise ExtractionException(f"OpenAI API did not return the expected function name. Expected: {tool_schema['name']}, actual: {function_name}")

        parameters = tool_schema["parameters"]
        arguments_str = function_call["arguments"]
        arguments = json.loads(arguments_str)

        missing_keys = LLMMethods.find_missing_keys(arguments, parameters)
        if len(missing_keys) > 0:
            logger.warning(f"OpenAI API did not return all the required arguments. Missing: {missing_keys}")
            if strict:
                raise ExtractionException(f"OpenAI API did not return all the required arguments. Missing: {missing_keys}")

        return arguments

    @staticmethod
    def find_missing_keys(json_obj: dict[str, any], schema: dict[str, any], path: list[str] | None = None) -> list[list[str]]:
        if path is None:
            path = list()

        missing_keys = list()

        if "properties" in schema:
            for key, value in schema["properties"].items():
                # Compute the JSON path for the current key
                key_path = path + [key]
                if "required" in schema and key in schema["required"] and key not in json_obj:
                    missing_keys.append(key_path)
                elif key in json_obj:
                    missing_keys += LLMMethods.find_missing_keys(json_obj[key], value, key_path)

        elif "items" in schema and isinstance(json_obj, list):
            for i, item in enumerate(json_obj):
                # Compute the JSON path for the current index in the array
                index_path = path + [str(i)]
                missing_keys += LLMMethods.find_missing_keys(item, schema['items'], index_path)

        return missing_keys

    @staticmethod
    def respond(prompt: str, message_history: list[dict[str, str]], function_id: str = "respond", **parameters: any) -> str:
        response = openai_chat(
            function_id,
            **parameters,
            messages=message_history + [{"role": "user", "content": prompt}],
            stream=False
        )

        response_message = response.choices[0]["message"]
        content = response_message["content"]
        return content.strip()

    @staticmethod
    def naturalize(request: str, tool_schema: dict[str, any], arguments_json: str, result_json: str, **parameters: any) -> str:
        tool_name = tool_schema["name"]
        messages = [
            {"role": "user", "content": request},
            {"role": "assistant", "content": None, "function_call": {"name": tool_name, "arguments": arguments_json}},
            {"role": "function", "name": tool_name, "content": result_json}
        ]

        response = openai_chat(
            "naturalize",
            **parameters,
            messages=messages,
            functions=[tool_schema],
            function_call="none",
        )

        response_message = response.choices[0]["message"]
        content = response_message["content"]
        return content.strip()

    @staticmethod
    def sample_first_action(request: str, **parameters: any) -> str:
        prompt = (
            f"## Request\n"
            f"{request.strip()}\n"
            f"\n"
            f"## Instructions\n"
            f"Think step-by-step: What would be a computer's first action in order to fulfill the request above? Provide a one-sentence command in "
            f"natural language for a single simple action towards fulfilling the request at hand.")

        response = LLMMethods.respond(prompt, list(), function_id="sample_first_step", **parameters)
        return response.strip()

    @staticmethod
    def sample_next_action(progress_report: str, **parameters: any) -> str:
        prompt = (
            f"<! -- BEGIN PROGRESS REPORT -->\n"
            f"{progress_report.strip()}\n"
            f"<! -- END PROGRESS REPORT -->\n"
            f"\n"
            f"# Instructions\n"
            f"Think step-by-step: Given the progress report above, what conclusions do you draw regarding the request? What would be a computer's next action in order "
            f"to fulfill the request? Provide a one-sentence command in natural language for a single simple action towards fulfilling the request at hand.\n"
            f"\n"
            f"Consider memorizing / recalling relevant information from previous steps.\n"
            f"\n"
            f"Check thoroughly if the request is _already_ fulfilled according to the progress report. In this case respond only with \"[FINALIZE]\".")
        response = LLMMethods.respond(prompt, list(), function_id="sample_next_step_summary", **parameters)
        return response.strip()

    @staticmethod
    def select_tool_name(toolbox: ToolBox, function_description: str) -> str | None:
        # get embedding for task_description
        embedding, = get_embeddings([function_description])

        # query for most similar function name
        (document_index,), (fitness,) = hyper_SVM_ranking_algorithm_sort(
            toolbox.vector_db.vectors,
            numpy.array(embedding),
            top_k=1,
            metric=toolbox.vector_db.similarity_metric
        )

        tool_name = toolbox.vector_db.documents[document_index]
        logger.info(f"Selected tool: {tool_name} with fitness {fitness:.2f}")

        if fitness < .9:
            return None

        return tool_name.strip()
