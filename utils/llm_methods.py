# coding=utf-8
import json
from abc import ABC
import logging

import hyperdb
import numpy
import openai
from hyperdb import hyper_SVM_ranking_algorithm_sort

from utils import openai_function_schemata
from utils.basic_llm_calls import openai_chat, get_embeddings
from utils.logging_handler import logging_handlers
from utils.misc import extract_docstring, format_steps
from utils.prompts import DOCSTRING_WRITER, REQUEST_IMPROVER
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
        return improved_request

    @staticmethod
    def summarize(text: str, instruction: str = "Summarize the text above.", **parameters: any) -> str:
        prompt = (f"{text}\n"
                  f"==============\n"
                  f"{instruction}\n")
        summary = LLMMethods.respond(prompt, list(), function_id="summarize", **parameters)
        return summary

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

        prompt = (f"{concatenated}\n"
                  f"===\n"
                  f"Given the text above, respond to the following request:\n"
                  f"{request}")

        response = LLMMethods.respond(prompt, list(), function_id="summarize", **parameters)
        return response

    @staticmethod
    def extract_arguments(full_description: str, tool_schema: dict[str, any], **parameters: any) -> dict[str, any]:
        response = openai_chat(
            f"extracting with `{tool_schema['name']}`",
            **parameters,
            messages=[{"role": "user", "content": full_description}],
            functions=[tool_schema],
            function_call={"name": tool_schema["name"]}
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
        if not all(each_argument in arguments for each_argument in parameters["required"]):
            raise ExtractionException(f"OpenAI API did not return the expected arguments. Expected: {tool_schema['parameters']['required']}, actual: {arguments}")

        return arguments

    @staticmethod
    def compose(request: str, previous_responses: list[str], **parameters: any) -> str:
        oai_intermediate = openai_function_schemata.get_intermediate_results
        arguments_json = json.dumps({"request": request})
        result_json = json.dumps(previous_responses)
        messages = [
            {"role": "user", "content": request},
            {"role": "assistant", "content": None, "function_call": {"name": oai_intermediate["name"], "arguments": arguments_json}},
            {"role": "function", "name": oai_intermediate["name"], "content": result_json}
        ]

        response = openai_chat(
            "compose",
            **parameters,
            messages=messages,
            functions=[oai_intermediate],
            function_call="none",
        )

        response_message = response.choices[0]["message"]
        content = response_message["content"]
        return content

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
        return content

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
        return content

    @staticmethod
    def sample_next_step(request: str, message_history: list[dict[str, str]], **parameters: any) -> str:
        prompt = (f"Request: {request}\n"
                  f"===\n"
                  f"\n")

        if len(message_history) < 1:
            prompt += (f"Think step-by-step: What would be a computer's first action in order to fulfill the request above? Provide a one-sentence command in "
                       f"natural language for a single simple action towards implementing the request at hand.")

        else:
            prompt += "Previous steps:\n"
            prompt += format_steps(message_history)
            prompt += (f"Think step-by-step: What would be a computer's next action in order to fulfill the request and given the previous steps above? Provide a "
                       f"one-sentence command in natural language for a single simple action towards implementing the request at hand. Finalize the response if the "
                       f"previous steps indicate that the request is already fulfilled.\n"
                       f"\n"
                       "Only describe the action, not the whole step or the result. If the last action has failed, do not instruct the exact same action again but "
                       "instead retry variants once or twice. If variants of the action fail as well, try a whole different approach instead.")

        response = LLMMethods.respond(prompt, list(), function_id="sample_next_step", **parameters)
        return response

    @staticmethod
    def sample_next_action_from_summary(request: str, history_summary: str, **parameters: any) -> str:
        prompt = (f"Request:\n"
                  f"{request}\n"
                  f"===\n"
                  f"\n")

        if 0 >= len(history_summary):
            prompt += (f"Think step-by-step: What would be a computer's first action in order to fulfill the request above? Provide a one-sentence command in "
                       f"natural language for a single simple action towards fulfilling the request at hand.")

        else:
            prompt += (f"Progress report:\n"
                       f"{history_summary}\n"
                       f"===\n"
                       f"\n")
            prompt += (f"Think step-by-step: Given the progress report, what conclusions do you draw with regarding the request above? What would be a computer's "
                       f"next action in order to fulfill the request? Provide a one-sentence command in natural language for a single simple action towards fulfilling "
                       f"the request at hand.\n"
                       f"\n"
                       # "If the previous action has failed according to the progress report, do not instruct the exact same action again but instead retry variants "
                       # "once or twice. If variants of the action fail as well, try a whole different approach instead.\n"
                       # "\n"
                       f"Finalize the response if the request is fulfilled according to the progress report.\n"
                       f"\n")
        response = LLMMethods.respond(prompt, list(), function_id="sample_next_step_summary", **parameters)
        return response

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

        return tool_name

    @staticmethod
    def make_function_docstring(task: str, **parameters: any) -> str:
        prompt = DOCSTRING_WRITER.format(task=task)

        history = list()

        response = LLMMethods.respond(prompt, history, function_id="make_function_docstring", **parameters)
        docstring = extract_docstring(response)
        return docstring
