# coding=utf-8
from __future__ import annotations
import dataclasses
import json
import logging
import os
import types
from traceback import format_exc

import colorama
import hyperdb
import numpy
from hyperdb import hyper_SVM_ranking_algorithm_sort

from utils.basic_llm_calls import openai_chat, get_embeddings
from utils.json_schemata import docstring_schema, proceed
from utils.llm_methods import LLMMethods, ExtractionException
from utils.prompts import CODER
from utils.logging_handler import logging_handlers
from utils.misc import truncate, extract_code_blocks, insert_docstring, compose_docstring, get_date_name, segment_text, LOGGER
from utils.toolbox import ToolBox, SchemaExtractionException


class ToolSelectionException(Exception):
    def __init__(self, message: str, data: dict[str, any] | None = None) -> None:
        super().__init__(message)
        self.data = data


class ToolApplicationException(Exception):
    def __init__(self, message: str, data: dict[str, any] | None = None) -> None:
        super().__init__(message)
        self.data = data


class ToolCreationException(Exception):
    def __init__(self, message: str, data: dict[str, any] | None = None) -> None:
        super().__init__(message)
        self.data = data or dict()


@dataclasses.dataclass
class ToolCall:
    tool_name: str
    input: dict[str, any]
    output: any


class StepProcessor:
    def __init__(self, toolbox: ToolBox, implementation_attempts: int = 3, result_limit: int = 2_000) -> None:
        self.toolbox = toolbox
        self.implementation_attempts = implementation_attempts
        self.result_limit = result_limit

    def _make_code(self, message_history: list[dict[str, any]]) -> str:
        response = openai_chat("make_code", messages=message_history, model="gpt-4")
        message = response["choices"][0]["message"]
        content = message["content"]

        tool_code = extract_code_blocks(content)[0]
        message_history.append(
            {"role": "assistant", "content": f"```python\n{tool_code}\n```"}
        )
        return tool_code

    def _confirmation(self, tool_call: str) -> bool:
        response = input(f"{colorama.Fore.YELLOW}{tool_call}{colorama.Style.RESET_ALL} [y/N]: ")
        return "y" == response.lower().strip()

    def apply_tool(self, tool: types.FunctionType, arguments: dict[str, any]) -> ToolCall:
        tool_name = tool.__name__

        truncated_arguments = ", ".join(f"str({k})={truncate(str(v), 50)!r}" for k, v in arguments.items())
        tool_call_str = f"{tool_name}({truncated_arguments})"

        if not self._confirmation(tool_call_str):
            del tool
            return ToolCall("reject", {"tool_call": tool_call_str}, "Tool call rejected by user.")

        result = tool(**arguments)
        return ToolCall(tool_name, arguments, result)

    def apply_new_tool(self, text: str, docstring_dict: dict[str, any]) -> ToolCall:
        tool_descriptions_string = self.toolbox.get_all_descriptions_string()
        docstring = compose_docstring(docstring_dict)
        code_prompt = CODER.format(tool_descriptions=tool_descriptions_string, docstring=docstring)
        message_history = [
            {"role": "user", "content": code_prompt}
        ]

        for i in range(self.implementation_attempts):
            print(f"{colorama.Back.YELLOW}New tool:{colorama.Style.RESET_ALL}")

            new_tool_code = self._make_code(message_history)
            new_tool_code = insert_docstring(new_tool_code, docstring)

            try:
                tmp_tool = self.toolbox.get_temp_tool_from_code(new_tool_code, docstring_dict)

            except Exception as e:
                msg = f"Tool creation failed: {e} ({i + 1} of {self.implementation_attempts} attempts)"
                LOGGER.error(msg)
                print(f"{colorama.Back.RED}{colorama.Style.DIM}{msg}{colorama.Style.RESET_ALL}")
                message_history.append(
                    {"role": "user", "content": format_exc()}
                )
                continue

            try:
                tool_schema = self.toolbox.get_tool_schema(new_tool_code, docstring_dict)

            except SchemaExtractionException as e:
                del tmp_tool
                msg = f"Schema extraction failed: {e} ({i + 1} of {self.implementation_attempts} attempts)"
                LOGGER.error(msg)
                print(f"{colorama.Back.RED}{colorama.Style.DIM}{msg}{colorama.Style.RESET_ALL}")
                continue

            try:
                arguments = LLMMethods.openai_extract_arguments(text, tool_schema)

            except ExtractionException as e:
                del tmp_tool
                msg = f"Argument extraction failed: {e} ({i + 1} of {self.implementation_attempts} attempts)"
                LOGGER.error(msg)
                print(f"{colorama.Back.RED}{colorama.Style.DIM}{msg}{colorama.Style.RESET_ALL}")
                continue

            try:
                tool_result = self.apply_tool(tmp_tool, arguments)
                del tmp_tool
                self.toolbox.save_tool_code(new_tool_code, docstring_dict, False)
                return tool_result

            except Exception as e:
                del tmp_tool
                msg = f"Tool application failed: {e} ({i + 1} of {self.implementation_attempts} attempts)"
                LOGGER.error(msg)
                print(f"{colorama.Back.RED}{colorama.Style.DIM}{msg}{colorama.Style.RESET_ALL}")
                message_history.append(
                    {"role": "user", "content": format_exc()}
                )
                continue

        return ToolCall("create_tool", {"description": docstring}, f"Tool creation failed after {self.implementation_attempts} attempts.")


class PerpetualAgent:
    def __init__(self, request: str, _previous_state: tuple[hyperdb.HyperDB, list[dict[str, any]], str] | None = None) -> None:
        self.main_logger = logging.getLogger()
        self.main_logger.setLevel(logging.INFO)
        for each_handler in logging_handlers():
            self.main_logger.addHandler(each_handler)

        self.toolbox = ToolBox("tools/")
        self.processor = StepProcessor(self.toolbox)

        self.request = request
        if _previous_state is None:
            self.facts_db, self.history, self.project_name = self.__initialize_new_project()
            self.project_directory = os.path.join("projects/", self.project_name)

            os.makedirs(self.project_directory)
            PerpetualAgent._save_request(self.request, self.project_directory)

        else:
            self.facts_db, self.history, self.project_name = _previous_state

        self.project_directory = os.path.join("projects/", self.project_name)

        self.progress = {
            "report": "No progress yet.",
            "was_step_effective": False,
            "is_done": False,
            "thought": "I should initiate the first step to fulfill the request."
        }

        self.last_action = ""
        self.last_fact = "No step has been taken yet."

    @staticmethod
    def load_project(project_name: str) -> PerpetualAgent:
        previous_state = PerpetualAgent.__read_project_data(project_name)
        return PerpetualAgent(project_name, _previous_state=previous_state)

    @staticmethod
    def _read_facts_db(project_directory: str) -> hyperdb.HyperDB:
        db = hyperdb.HyperDB()
        facts_path = os.path.join(project_directory, "facts_db.pickle.gz")
        db.load(facts_path)
        return db

    @staticmethod
    def _read_history(project_directory: str) -> list[dict[str, any]]:
        history_path = os.path.join(project_directory, "history.json")
        with open(history_path, mode="r") as file:
            history = list()
            for each_line in file:
                fact = json.loads(each_line)
                assert isinstance(fact, dict)
                history.append(fact)
        return history

    @staticmethod
    def _read_request(project_directory: str) -> str:
        request_path = os.path.join(project_directory, "request.txt")
        with open(request_path, mode="r") as file:
            request = file.read()
        return request

    @staticmethod
    def _save_messages(history: list[dict[str, any]], project_directory: str) -> None:
        history_path = os.path.join(project_directory, "history.jsonl")
        with open(history_path, mode="a") as file:
            for each_message in history:
                json.dump(each_message, file)
                file.write("\n")

    def _save_facts(self, thought: str, tool_call: ToolCall, facts_db: hyperdb.HyperDB, project_directory: str) -> None:
        no_facts = len(facts_db.documents)
        facts = list()
        for i, each_segment in enumerate(segment_text(str(tool_call.output), segment_length=1_000)):
            fact = LLMMethods.naturalize(thought, each_segment, model="gpt-3.5-turbo")
            fact_json = {"content": fact, "index": i + no_facts}
            facts.append(fact_json)

        embeddings = get_embeddings([each_fact["content"] for each_fact in facts])
        facts_json = [json.dumps(each_fact) for each_fact in facts]
        facts_db.add_documents(facts_json, vectors=embeddings)
        facts_path = os.path.join(project_directory, "facts_db.pickle.gz")
        facts_db.save(facts_path)

        facts_path = os.path.join(project_directory, "facts.jsonl")
        with open(facts_path, mode="a") as file:
            for each_fact in facts_json:
                file.write(each_fact)
                file.write("\n")

    @staticmethod
    def _save_request(request: str, project_directory: str) -> None:
        request_path = os.path.join(project_directory, "request.txt")
        with open(request_path, mode="w") as file:
            file.write(request)

    def __initialize_new_project(self) -> tuple[hyperdb.HyperDB(), list[dict[str, any]], str]:
        project_name = get_date_name()
        self.main_logger.info(f"Starting new project '{project_name}'.")
        facts_db = hyperdb.HyperDB()
        history = list()
        return facts_db, history, project_name

    @staticmethod
    def __read_project_data(project_name: str) -> tuple[hyperdb.HyperDB(), list[dict[str, any]], str]:
        project_directory = os.path.join("projects/", project_name)
        db = PerpetualAgent._read_facts_db(project_directory)
        history = PerpetualAgent._read_history(project_directory)
        request = PerpetualAgent._read_request(project_directory)
        return db, history, request

    def _save_state(self, thought: str, tool_call: ToolCall, last_exchange: list[dict[str, any]]) -> None:
        self.main_logger.info(f"Starting project at '{self.project_directory}'.")

        self._save_facts(thought, tool_call, self.facts_db, self.project_directory)
        PerpetualAgent._save_messages(last_exchange, self.project_directory)

    def _summarize_facts(self, thought: str, n: int = 5) -> str:
        embedding, = get_embeddings([thought])
        no_documents = len(self.facts_db.documents)
        document_indices, fitnesses = hyper_SVM_ranking_algorithm_sort(
            self.facts_db.vectors,
            numpy.array(embedding),
            top_k=no_documents,
            metric=self.facts_db.similarity_metric
        )

        new_fitness = list()
        for each_index, each_fitness in zip(document_indices, fitnesses):
            each_document = self.facts_db.documents[each_index]
            each_dict = json.loads(each_document)
            each_index = each_dict["index"]
            backwards_index = no_documents - each_index
            prioritized_fitness = each_fitness / backwards_index
            each_dict["prioritized_fitness"] = prioritized_fitness
            new_fitness.append(each_dict)

        new_fitness.sort(key=lambda x: x["prioritized_fitness"], reverse=True)
        relevant_facts = "\n\n".join(each_document["content"] for each_document in new_fitness[:n])
        prompt = (
            f"<!-- BEGIN FACTS -->\n"
            f"{relevant_facts}\n"
            f"<!-- END FACTS -->\n"
            f"\n"
            f"Summarize the facts. Take care to preserve literal information."
        )

        response = LLMMethods.respond(prompt, list(), function_id="summarize", model="gpt-3.5-turbo")
        return response

    def _naturalize(self, thought: str, tool_call: ToolCall) -> str:
        action = tool_call.tool_name
        arguments = tool_call.input
        observation_json = json.dumps(tool_call.output)

        if len(observation_json) >= 5_000:
            fact = LLMMethods.vector_summarize(thought, observation_json, model="gpt-3.5-turbo")
            return fact

        arguments_json = json.dumps(arguments)
        action_schema = self.toolbox.get_schema_from_name(action)
        fact = LLMMethods.openai_naturalize(thought, action_schema, arguments_json, observation_json, model="gpt-3.5-turbo")
        return fact

    def implement_thought(self, thought: str, summary: str) -> ToolCall:
        try:
            docstring_dict = LLMMethods.openai_extract_arguments(thought, docstring_schema, strict=True, model="gpt-4-0613")

        except ExtractionException as e:
            raise ToolSelectionException("Error while extracting docstring.") from e

        description = self.toolbox.description_from_docstring_dict(docstring_dict)
        tool_name, fitness = LLMMethods.select_tool_name(self.toolbox, description)

        msg = f"Found tool `{tool_name}` with a fitness of {fitness:.2f}"
        self.main_logger.info(msg)
        print(f"{colorama.Fore.MAGENTA}{msg}{colorama.Style.RESET_ALL}")

        if fitness < .9:
            tool_call = self.processor.apply_new_tool(summary, docstring_dict)
            return tool_call

        print(f"{colorama.Back.YELLOW}Tool:{colorama.Style.RESET_ALL}")
        tool = self.toolbox.get_tool_from_name(tool_name)
        tool_schema = self.toolbox.get_schema_from_name(tool_name)
        arguments = LLMMethods.openai_extract_arguments(summary, tool_schema)
        try:
            tool_call = self.processor.apply_tool(tool, arguments)

        except Exception as e:
            result = f"Error during execution: {e}"
            self.main_logger.error(result)
            print(f"{colorama.Fore.RED}{result}{colorama.Style.RESET_ALL}")
            return ToolCall("tool_execution", {"tool_name": tool_name, "arguments": arguments}, e)

        return tool_call

    def process(self) -> str:
        # "gpt-3.5-turbo-16k-0613", "gpt-4-32k-0613", "gpt-4-0613", "gpt-3.5-turbo-0613"

        while not self.progress["is_done"]:
            data_prompt = {"request": self.request, "last_step": self.last_fact}
            prompt = (
                f"```json\n"
                f"{json.dumps(data_prompt, indent=4, sort_keys=True)}\n"
                f"```"
            )
            progress = LLMMethods.openai_extract_arguments(prompt, proceed, history=self.history, model="gpt-4-0613")
            if progress["is_done"]:
                break

            if 0 < len(self.last_action):
                self.toolbox.update_tool_stats(self.last_action, progress["was_step_effective"])

            thought = progress["thought"]
            print(
                f"{colorama.Back.BLUE}Thought:{colorama.Style.RESET_ALL}\n"
                f"{colorama.Fore.BLUE}{thought}{colorama.Style.RESET_ALL}"
            )

            if len(self.facts_db.documents) < 1:
                summary = (
                    f"{self.request}\n\n"
                    f"{thought}"
                )
            else:
                summary = self._summarize_facts(thought)

            tool_call = self.implement_thought(thought, summary)
            print(
                f"{colorama.Back.CYAN}Observation:{colorama.Style.RESET_ALL}\n"
                f"{colorama.Fore.CYAN}{tool_call.output}{colorama.Style.RESET_ALL}"
            )
            if tool_call.tool_name in {"reject", "create_tool", "tool_execution"}:
                self.last_fact = LLMMethods.naturalize(thought, tool_call.output, model="gpt-3.5-turbo")
            else:
                self.last_fact = self._naturalize(thought, tool_call)
                # if len(tool_output) >= 5_000:
                #   naturalize and shorten tool output for summary
                #   segment and naturalize for long term memory

            self.last_action = tool_call.tool_name
            self._save_state(thought, tool_call, self.history[:-2])

        return self.progress["report"]
