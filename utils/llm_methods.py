# coding=utf-8
import json
import time
import types
from abc import ABC
import logging

import numpy
import openai
from hyperdb import hyper_SVM_ranking_algorithm_sort
from openai.openai_object import OpenAIObject

from utils import openai_function_schemata
from utils.logging_handler import logging_handlers
from utils.misc import extract_code_blocks
from utils.toolbox import ToolBox

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handlers = logging_handlers()
for each_handler in handlers:
    logger.addHandler(each_handler)


def openai_chat(function_id: str, *args: any, **kwargs: any) -> OpenAIObject:
    while True:
        for i in range(5):
            try:
                logger.info(f"Calling OpenAI API: {function_id}")
                logger.debug(f"OpenAI API: args={args}, kwargs={kwargs}")
                response = openai.ChatCompletion.create(*args, **kwargs)
                return response

            except Exception as e:
                logger.error(str(e))
                msg = f"Error. Retrying chat completion {i + 1} of 5"
                logger.error(msg)
                print(msg)
                time.sleep(1)
                continue

        input("Chat completion failed. Press enter to retry...")


def get_embeddings(segments: list[str]) -> list[list[float]]:
    model = "text-embedding-ada-002"  # max input tokens: 8191, dimensions: 1536
    # model = "text-similarity-davinci-001"
    # model = "text-similarity-curie-001"
    # model = "text-similarity-babbage-001"
    # model = "text-similarity-ada-001"

    while True:
        for i in range(5):
            try:
                result = openai.Embedding.create(
                    input=segments,
                    model=model,
                )
                return [record["embedding"] for record in result["data"]]

            except Exception as e:
                logger.error(str(e))
                msg = f"Error. Retrying embedding {i+1} of 5"
                logger.error(msg)
                print(msg)
                time.sleep(1)
                continue

        input("Embedding retrieval failed. Press enter to retry...")


def print_stream(stream: OpenAIObject) -> str:
    full_content = list()
    for chunk in stream:
        delta = chunk["choices"][0]["delta"]
        msg = delta.get("content", "")
        full_content.append(msg)
        print(msg, end="")
    print()
    return "".join(full_content)


class ExtractionException(Exception):
    pass


class LLMMethods(ABC):
    openai.api_key_path = "resources/openai_api_key.txt"

    @staticmethod
    def extract_arguments(previous_messages: list[dict[str, str]], tool_schema: dict[str, any], prompt: str | None = None, **parameters: any) -> dict[str, any]:
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
    def sample_next_step(request: str, message_history: list[dict[str, str]], toolbox: ToolBox, **parameters: any) -> str:
        previous_steps = list()

        actions = "\n".join(f"- {toolbox.get_schema_from_name(each_action)['description']}" for each_action in toolbox.get_all_tools())
        action_section = f"Actions:\n{actions}\n===\n"

        if len(message_history) < 1:
            previous_steps.append(f"Request: {request}\n===\n")
            previous_steps.append(action_section)
            previous_steps.append("What would be a reasonable first action considering the available actions and previous steps towards fulfilling the request above? "
                                  "Provide a one-sentence instruction that applies one action to the request at hand.\n"
                                  "Do not use multiple actions (e.g. by combining actions with \"and\"). Do not instruct dealing with more than one thing at a time "
                                  "but deal with each thing in its own individual action.")

        else:
            for i in range(0, len(message_history), 2):
                each_request, each_response = tuple(each_message["content"] for each_message in message_history[i:i + 2])
                each_step = (f"Step {i // 2 + 1}:\n"
                             f"  Action: {each_request.strip()}\n"
                             f"  Result: {each_response.strip()}\n"
                             f"===\n")

                previous_steps.append(each_step)

            previous_steps.append(f"Request: {request}\n===\n")
            previous_steps.append(action_section)
            previous_steps.append(f"What would be a reasonable action for the next step towards fulfilling the request considering the available actions and the "
                                  f"previous steps above? Provide a one-sentence instruction that applies one action to the request at hand. Use the results of "
                                  f"previous actions to inform your choice. Finalize the response if the intermediate results of the previous steps fulfill the "
                                  f"request.\n"
                                  "Do not instruct multiple actions (e.g. by combining actions with \"and\"). Do not instruct dealing with more than one thing at a time "
                                  "but deal with each thing in one individual action. Do not repeat the last action, if it was successful. Do not provide a result. If "
                                  "the last action has failed, do not suggest the exact same action again but instead retry variants once or twice. If variants of the "
                                  "action fail as well, try a whole other approach instead.\n")

        prompt = "".join(previous_steps)

        response = LLMMethods.respond(prompt, list(), function_id="sample_next_step", **parameters)
        return response

    @staticmethod
    def _sample_next_step(request: str, message_history: list[dict[str, str]], **parameters: any) -> str | None:
        instruction = f"Think step-by-step: Given the information above, what is the next single small action to perform to fulfill the request?\n" \
                      f"Provide a one sentence instruction describing a logical action towards fulfilling the request. Break the task down in small steps.\n" \
                      f"Do not combine multiple actions. Do not repeat the last action, if it was successful. If an action has failed, retry it once or twice but do " \
                      f"not suggest the exact same action again. If an action fails repeatedly, try another approach instead.\n" \
                      f"If the request is already fulfilled, return \"[request fulfilled]\"."

        prompt = (f"Request:\n"
                  f"{request}\n"
                  f"==============\n"
                  f"{instruction}")

        response = LLMMethods.respond(prompt, message_history, function_id="sample_next_step", **parameters)
        if "[request fulfilled]" in response.lower():
            return None

        return response

    @staticmethod
    def select_tool_call(toolbox: ToolBox,
                         task_description: str,
                         message_history: list[dict[str, str]] | None = None,
                         **parameters: any) -> tuple[types.FunctionType, dict[str, any]] | None:

        # todo: vectorize? con: losing api advantage, pro: unlimited number of tools

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
    def select_tool_call_from_db(toolbox: ToolBox,
                                 task_description: str,
                                 message_history: list[dict[str, str]] | None = None,
                                 **parameters: any) -> tuple[types.FunctionType, dict[str, any]] | None:

        # todo: make task description general. for example: "Describe a Python function that could be used to solve the task. Take care to: []"
        """
        Provide a more extensive and detailed Google style docstring for the function above that makes clear in which particular cases the function can be applied. Include the sections "Example", "Args", and "Returns".

        Don't mention the name of the function.
        Don't mention individual use cases or contexts but provide a general and clear description so it is clear which use cases and contexts it applies to.
        Don't describe the process as it is formalized in code.
        Describe the function the code provides, do not describe how this function is achieved.

        Keep below 500 characters.
        """

        # get embedding for task_description
        embedding, = get_embeddings([task_description])

        # query for most similar function name
        (tool_name,), (fitness,) = hyper_SVM_ranking_algorithm_sort(
            toolbox.vector_db.vectors,
            numpy.array(embedding),
            top_k=1,
            metric=toolbox.vector_db.similarity_metric
        )

        if fitness < .9:
            return None

        tool_schema = toolbox.get_schema_from_name(tool_name)
        arguments = LLMMethods.extract_arguments(message_history, tool_schema, model="gpt-3.5-turbo-0613", **parameters)

        all_tools = toolbox.get_all_tools()
        tool = all_tools[tool_name]
        return tool, arguments

    @staticmethod
    def make_tool_code(toolbox: ToolBox, description: str, message_history: list[dict[str, str]] | None = None, **parameters: any) -> str:
        all_tools = toolbox.get_all_tools()
        tool_description_lines = [toolbox.get_description_from_name(each_name) for each_name in all_tools]
        tool_descriptions = "\n".join(f"- {each_description}" for each_description in tool_description_lines)

        prompt = (f"Task:\n"
                  f"{description}\n"
                  f"=================\n"
                  f"Available helper functions:\n"
                  f"{tool_descriptions}\n"
                  f"=================\n\n")

        # todo generate google style docstring separately from prompt above, take existing functions as examples
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
