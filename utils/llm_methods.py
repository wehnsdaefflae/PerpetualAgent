# coding=utf-8
import json
import types
from abc import ABC
import logging

import hyperdb
import numpy
import openai
from hyperdb import hyper_SVM_ranking_algorithm_sort

from utils import openai_function_schemata
from utils.basic_llm_calls import openai_chat, get_embeddings
from utils.logging_handler import logging_handlers
from utils.misc import extract_code_blocks, extract_docstring
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
        prompt = (f"Request:\n"
                  f"{main_request}\n"
                  f"==============\n"
                  f"Provide an improved version of this request by incorporating the following points:\n"
                  f"1. Identify the Purpose of the Request: What is the objective of the request? Understand the aim behind the request. This will give the instruction "
                  f"a clear direction.\n"
                  f"2. Specify the Action: What needs to be done? The action should be clearly defined. Instead of saying \"improve the report\", say \"add more data "
                  f"analysis and revise the formatting of the report.\"\n"
                  f"3. Details Matter: Give as much detail as you can. Be specific about what exactly needs to be done. Use precise, concrete language.\n"
                  f"4. Define the Scope: What is the extent of the request? For instance, does the request pertain to one particular chapter of a report or the entire "
                  f"report?\n"
                  f"5. Indicate the Format: If there is a specific way to fulfill the request, provide this information. For example, if you are requesting a report, "
                  f"specify whether you want it in Word, PDF, or another format.\n"
                  f"6. Clarify the Success Criteria: How will you judge whether the request has been fulfilled? What does the end result look like? It's important to "
                  f"convey your expectations.\n"
                  f"7. Address Potential Challenges: Think about the possible difficulties in fulfilling the request, and provide solutions or suggestions on how to "
                  f"deal with them.\n"
                  f"8. Provide Resources or Assistance if Needed: If there are any tools, references, or people that might help fulfill the request, mention them.\n"
                  f"\n"
                  f"Respond only with the improved version of the request. Make it concise and to the point. Write between two and five sentences, do not use bullet "
                  f"points, do not address the points above explicitly, do not include any of the above points in your response, and do not encourage checking back. "
                  f"They're on their own on this one.\n")
        improved_request = LLMMethods.respond(prompt, list(), *parameters, **kwargs)
        return improved_request

    @staticmethod
    def summarize(request: str, text: str, segment_size: int = 500, overlap: int = 100, nearest_neighbors: int = 5, **parameters: any) -> str:
        # segment text
        len_text = len(text)
        segments = [text[max(0, i - overlap):min(i + segment_size + overlap, len_text)].strip() for i in range(0, len_text, segment_size)]
        print(f"Summarizing {len(segments)}...")

        for i in range(len(segments)):
            if i >= 1:
                segments[i] = "[...]" + segments[i]

            if i < len(segments) - 1:
                segments[i] += "[...]"

        db = hyperdb.HyperDB()

        # embed
        embeddings = get_embeddings([request] + segments)

        request_vector = embeddings[0]
        segment_vectors = embeddings[1:]

        # put embeddings in database
        db.add_documents(segments, vectors=segment_vectors)

        # get nearest neighbors
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
    def extract_arguments(previous_messages: list[dict[str, str]], tool_schema: dict[str, any], prompt: str, **parameters: any) -> dict[str, any]:
        response = openai_chat(
            f"extracting with `{tool_schema['name']}`",
            **parameters,
            messages=previous_messages + [{"role": "user", "content": prompt}],
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
            previous_steps = list()
            for i in range(0, len(message_history[-10:]), 2):
                each_request, each_response = tuple(each_message["content"] for each_message in message_history[i:i + 2])
                each_step = (f"Step {i // 2 + 1}:\n"
                             f"  Action: {each_request.strip()}\n"
                             f"  Result: {each_response.strip()}\n"
                             f"===\n")

                previous_steps.append(each_step)

            prompt += "\n".join(previous_steps)
            prompt += (f"Think step-by-step: What would be a computer's next action in order to fulfill the request and given the previous steps above? Provide a "
                       f"one-sentence command in natural language for a single simple action towards implementing the request at hand. Finalize the response if the "
                       f"previous steps indicate that the request is already fulfilled.\n"
                       f"\n"
                       "Only describe the action, not the whole step or the result. If the last action has failed, do not instruct the exact same action again but "
                       "instead retry variants once or twice. If variants of the action fail as well, try a whole different approach instead.")

        response = LLMMethods.respond(prompt, list(), function_id="sample_next_step", **parameters)
        return response

    @staticmethod
    def _sample_next_step(request: str, message_history: list[dict[str, str]], **parameters: any) -> str | None:
        prompt = (f"Request:\n"
                  f"{request}\n"
                  f"===========\n"
                  f"Think step-by-step: Given the information above, what is the next single small action to perform to fulfill the request?\n"
                  f"Provide a one sentence instruction describing a logical action towards fulfilling the request. Break the task down in small steps.\n"
                  f"Do not combine multiple actions. Do not repeat the last action, if it was successful. If an action has failed, retry it once or twice but do "
                  f"not suggest the exact same action again. If an action fails repeatedly, try another approach instead.")

        response = LLMMethods.respond(prompt, message_history, function_id="sample_next_step", **parameters)
        return response

    @staticmethod
    def _select_tool_call(toolbox: ToolBox,
                          task_description: str,
                          message_history: list[dict[str, str]] | None = None,
                          **parameters: any) -> tuple[types.FunctionType, dict[str, any]] | None:

        all_tools = toolbox.get_all_tools()
        all_tool_schemata = [toolbox.get_schema_from_name(each_name) for each_name in all_tools]

        response = openai_chat(
            "select_tool_args",
            **parameters,
            messages=message_history + [{"role": "user", "content": task_description}],
            functions=all_tool_schemata
        )

        each_choice, = response.choices
        # check response. if finish_reason is not "function_call", create new tool (simple requests are covered by `common_sense`)
        finish_reason = each_choice["finish_reason"]
        if finish_reason != "function_call":
            return None

        response_message = each_choice["message"]
        function_call = response_message["function_call"]
        function_name = function_call["name"]
        if function_name not in all_tools or function_name == "general_solver":
            return None

        arguments_str = function_call["arguments"]
        arguments = json.loads(arguments_str)
        tool = all_tools[function_name]
        return tool, arguments

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

        if fitness < .8:
            return None

        return tool_name

    @staticmethod
    def _make_tool_code(toolbox: ToolBox, description: str, message_history: list[dict[str, str]] | None = None, **parameters: any) -> str:
        all_tools = toolbox.get_all_tools()
        tool_description_lines = [toolbox.get_description_from_name(each_name) for each_name in all_tools]
        tool_descriptions = "\n".join(f"- {each_description}" for each_description in tool_description_lines)

        prompt = (f"Task:\n"
                  f"{description}\n"
                  f"=================\n"
                  f"Available helper functions:\n"
                  f"{tool_descriptions}\n"
                  f"=================\n\n")

        # todo generate google style docstring separately gpt-3.5-turbo from prompt above, take existing functions as examples
        instruction = "Implement a Python function that achieves the task described above. Provide a parametrized function that is general enough to be used in other " \
                      "contexts beyond the particular task at hand. " \
                      "Give it a name that is precise so as to later recognise what it does. Don't use one of the helper function names as a name for the function. " \
                      "The function must be type hinted and feature a detailed Google doc string with the sections \"Example\", \"Args\", and  \"Returns\". " \
                      "Call the available helper functions from the list above, whenever possible. Helper functions are imported like `from tools.calculate import " \
                      "calculate`. " \
                      "Do not use placeholders or variables that the user needs to fill in (e.g. API keys). Make sure, the function works out-of-the-box, " \
                      "without any user information, interaction, or modification." \
                      "Respond with only a single Python code block containing the function as well as the required imports. Do not generate code outside of the " \
                      "function body except the necessary imports."

        prompt += instruction

        history = list() if message_history is None else list(message_history)

        response = LLMMethods.respond(prompt, history, function_id="make_tool_code", **parameters)
        code = extract_code_blocks(response)
        return code[0]

    @staticmethod
    def make_code(toolbox: ToolBox, docstring: str, message_history: list[dict[str, str]] | None = None, **parameters: any) -> str:
        all_tools = toolbox.get_all_tools()
        tool_description_lines = [toolbox.get_description_from_name(each_name) for each_name in all_tools]
        tool_descriptions = "\n".join(f"- {each_description}" for each_description in tool_description_lines)

        prompt = (f"Available helper functions:\n"
                  f"{tool_descriptions}\n"
                  f"=================\n"
                  f"Docstring:\n"
                  f"{docstring}\n"
                  f"=================\n"
                  "Generate a Python function that fully implements the docstring above. Make it general enough to be used in diverse use cases and contexts. The "
                  "function must be type hinted, working, and every aspect must be implement according to the docstring.\n"
                  "\n"
                  "Make use of the available helper functions from the list above by importing them from the tools module (e.g. for the calculate tool: `from "
                  "tools.calculate import calculate`).\n"
                  "\n"
                  "Do not use placeholders that must be filled in later (e.g. API keys).\n"
                  "\n"
                  "Respond with a single Python code block containing only the required imports as well as the function including the above docstring. Format the "
                  "docstring according to the Google style guide.\n")

        history = list() if message_history is None else list(message_history)

        response = LLMMethods.respond(prompt, history, function_id="make_code", **parameters)
        code = extract_code_blocks(response)
        return code[0]

    @staticmethod
    def make_function_docstring(task: str, **parameters: any) -> str:
        prompt = (f"Task:\n"
                  f"{task}\n"
                  f"===\n"
                  "\n"
                  "Generate a Google style docstring in triple quotation marks for a Python function that could solve the task above. Describe the function as if it "
                  "already existed. Make it is easy to infer from the description which use cases and contexts the function can be applied to. Use function arguments to "
                  "make sure that the function can be applied to other tasks as well.\n"
                  "\n"
                  "The docstring must contain a function description, as well as the sections \"Example\", \"Args\", and \"Returns\".\n"
                  "\n"
                  "Call the function in the Example section like so: `>>> function_name(<arguments>)` Provide only one example with arguments for a representative use "
                  "case. Do not show the return value of the function call.\n"
                  "\n"
                  "Do not mention particular use cases or contexts in the description.\n"
                  "Mention the name of the function only in the Example section but not in the description.\n"
                  "Describe what the function does, not how it is done.\n"
                  f"\n"
                  f"Keep it below 500 characters.")

        history = list()

        response = LLMMethods.respond(prompt, history, function_id="make_function_docstring", **parameters)
        docstring = extract_docstring(response)
        return docstring
