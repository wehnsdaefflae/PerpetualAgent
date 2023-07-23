# coding=utf-8
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
from utils.misc import truncate, extract_code_blocks, insert_docstring, compose_docstring, get_date_name
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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        for each_handler in logging_handlers():
            self.logger.addHandler(each_handler)

        self.toolbox = toolbox
        self.implementation_attempts = implementation_attempts
        self.result_limit = result_limit

    def _make_code(self, message_history: list[dict[str, any]], docstring_dict: dict[str, any]) -> str:
        response = openai_chat("make_code", messages=message_history, model="gpt-4")
        message = response["choices"][0]["message"]
        content = message["content"]

        try:
            tool_code = extract_code_blocks(content)[0]
            _ = self.toolbox.get_temp_tool_from_code(tool_code, docstring_dict)
            message_history.append(
                {"role": "assistant", "content": f"```python\n{tool_code}\n```"}
            )
            return tool_code

        except Exception as e:
            self.logger.error(f"Error while extracting tool code: {e}")
            raise ToolCreationException("Error while extracting tool code.") from e

    def _confirmation(self, tool_call: str) -> bool:
        response = input(f"{colorama.Fore.RED}{tool_call}{colorama.Style.RESET_ALL} [y/N]: ")
        return "y" == response.lower().strip()

    def apply_tool(self, tool: types.FunctionType, arguments: dict[str, any], is_temp_tool: bool) -> ToolCall:
        tool_name = tool.__name__

        truncated_arguments = ", ".join(f"str({k})={truncate(str(v), 50)!r}" for k, v in arguments.items())
        tool_call = f"{tool_name}({truncated_arguments})"

        if not self._confirmation(tool_call):
            del tool
            return ToolCall("reject", {"tool_call": tool_call}, "Tool call rejected.")

        try:
            result = tool(**arguments)

        except Exception as e:
            trace = format_exc()
            result = f"{tool_call}: Error during execution. {e}\n{trace}"
            self.logger.error(result)
            if is_temp_tool:
                self.logger.error(trace)
                return ToolCall("execution", {"tool_call": tool_call}, result)

        finally:
            del tool

        return ToolCall(tool_name, arguments, result)

    def apply_new_tool(self, text: str, docstring_dict: dict[str, any]) -> ToolCall:
        tool_descriptions_string = self.toolbox.get_all_descriptions_string()
        docstring = compose_docstring(docstring_dict)
        code_prompt = CODER.format(tool_descriptions=tool_descriptions_string, docstring=docstring)
        message_history = [
            {"role": "user", "content": code_prompt}
        ]

        for _ in range(self.implementation_attempts):
            try:
                new_tool_code = self._make_code(message_history, docstring_dict)
                new_tool_code = insert_docstring(new_tool_code, docstring)
                tmp_tool = self.toolbox.get_temp_tool_from_code(new_tool_code, docstring_dict)

            except ToolCreationException as e:
                self.logger.error(e)
                return ToolCall("tool_creation", {"description": docstring}, e.__cause__ if e.__cause__ else e)

            try:
                tool_schema = self.toolbox.get_schema_from_code(new_tool_code, docstring_dict)

            except SchemaExtractionException as e:
                self.logger.error(e)
                return ToolCall("schema_extraction", {"code": new_tool_code, "description": docstring}, e.__cause__ if e.__cause__ else e)

            try:
                arguments = LLMMethods.openai_extract_arguments(text, tool_schema, model="gpt-3.5-turbo-0613")

            except ExtractionException as e:
                self.logger.error(e)
                return ToolCall("argument_extraction", {"information": text, "json_schema": tool_schema}, e.__cause__ if e.__cause__ else e)

            print(f"{colorama.Back.RED}New tool:{colorama.Style.RESET_ALL}")
            tool_result = self.apply_tool(tmp_tool, arguments, True)
            if tool_result.tool_name != "reject" and tool_result.tool_name != "execution":
                self.toolbox.save_tool_code(new_tool_code, docstring_dict, False)
                return tool_result

            message_history.append(
                {"role": "user", "content": tool_result.output}
            )

        return ToolCall("tool_execution", {"description": docstring}, f"Execution failed after {self.implementation_attempts} attempts.")


class PerpetualAgent:
    def __init__(self) -> None:
        self.main_logger = logging.getLogger()
        self.main_logger.setLevel(logging.INFO)
        for each_handler in logging_handlers():
            self.main_logger.addHandler(each_handler)

        self.toolbox = ToolBox("tools/")
        self.processor = StepProcessor(self.toolbox)

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
    def _read_progress(project_directory: str) -> dict[str, any]:
        progress_path = os.path.join(project_directory, "progress.json")
        with open(progress_path, mode="r") as file:
            progress = json.load(file)
            assert isinstance(progress, dict)
        return progress

    @staticmethod
    def _read_request(project_directory: str) -> str:
        request_path = os.path.join(project_directory, "request.txt")
        with open(request_path, mode="r") as file:
            request = file.read()
        return request

    @staticmethod
    def _save_history(history: list[dict[str, any]], project_directory: str) -> None:
        history_path = os.path.join(project_directory, "history.json")
        with open(history_path, mode="w") as file:
            for each_fact in history:
                json.dump(each_fact, file, indent=4, sort_keys=True)
                file.write("\n")

    @staticmethod
    def _save_progress(progress: dict[str, any], project_directory: str) -> None:
        progress_path = os.path.join(project_directory, "progress.json")
        with open(progress_path, mode="w") as file:
            json.dump(progress, file, indent=4, sort_keys=True)

    @staticmethod
    def _save_fact(fact: str, facts_db: hyperdb.HyperDB, project_directory: str) -> None:
        embedding, = get_embeddings([fact])
        no_facts = len(facts_db.documents)
        fact_json = json.dumps(
            {"fact": fact, "index": no_facts},
            indent=4,
            sort_keys=True
        )
        facts_db.add_document(fact_json, embedding)
        facts_path = os.path.join(project_directory, "facts_db.pickle.gz")
        facts_db.save(facts_path)

        facts_path = os.path.join(project_directory, "facts.json")
        with open(facts_path, mode="a") as file:
            json.dump(fact, file, indent=4, sort_keys=True)
            file.write("\n")

    @staticmethod
    def _save_request(request: str, project_directory: str) -> None:
        request_path = os.path.join(project_directory, "request.txt")
        with open(request_path, mode="w") as file:
            file.write(request)

    def _initialize_new_project(self) -> tuple[hyperdb.HyperDB(), list[dict[str, any]], dict[str, any], str]:
        project_name = get_date_name()
        self.main_logger.info(f"Starting new project '{project_name}'.")
        facts_db = hyperdb.HyperDB()
        progress = {"report": "No progress yet.", "eas_step_effective": False, "is_done": False, "thought": "I should initiate the first step to fulfill the request."}
        history = list()
        return facts_db, history, progress, project_name

    def _read_project_data(self, project_name: str) -> tuple[hyperdb.HyperDB(), list[dict[str, any]], dict[str, any], str]:
        project_directory = os.path.join("projects/", project_name)
        self.main_logger.info(f"Continuing project from '{project_directory}'.")

        db = PerpetualAgent._read_facts_db(project_directory)
        progress = PerpetualAgent._read_progress(project_directory)
        history = PerpetualAgent._read_history(project_directory)
        request = PerpetualAgent._read_request(project_directory)
        return db, history, progress, request

    def _save_project(self, project_name: str, request: str, progress: dict[str, any], facts_db: hyperdb.HyperDB(), fact: str, history: list[dict[str, any]]) -> None:
        project_directory = os.path.join("projects/", project_name)
        self.main_logger.info(f"Starting project at '{project_directory}'.")

        os.makedirs(project_directory)

        PerpetualAgent._save_request(request, project_directory)
        PerpetualAgent._save_fact(fact, facts_db, project_directory)
        PerpetualAgent._save_progress(progress, project_directory)
        PerpetualAgent._save_history(history, project_directory)

    def load_project(self, project_name: str) -> str:
        facts_db, history, progress, request = self._read_project_data(project_name)
        return self._process_request(project_name, request, progress, facts_db, history)

    def new_project(self, request: str) -> str:
        facts_db, history, progress, project_name = self._initialize_new_project()
        return self._process_request(project_name, request, progress, facts_db, history)

    def summarize(self, facts_db: hyperdb.HyperDB(), thought: str, n: int = 5) -> str:
        embedding, = get_embeddings([thought])
        no_documents = len(facts_db.documents)
        document_indices, fitnesses = hyper_SVM_ranking_algorithm_sort(
            facts_db.vectors,
            numpy.array(embedding),
            top_k=no_documents,
            metric=facts_db.similarity_metric
        )

        new_fitness = list()
        for each_index, each_fitness in zip(document_indices, fitnesses):
            each_document = facts_db.documents[each_index]
            each_dict = json.loads(each_document)
            each_index = each_dict["index"]
            backwards_index = no_documents - each_index
            prioritized_fitness = each_fitness / backwards_index
            each_dict["prioritized_fitness"] = prioritized_fitness
            new_fitness.append(each_dict)

        new_fitness.sort(key=lambda x: x["prioritized_fitness"], reverse=True)
        relevant_facts = "\n\n".join(each_document["fact"] for each_document in new_fitness[:n])
        prompt = (
            f"<!-- BEGIN FACTS -->\n"
            f"{relevant_facts}\n"
            f"<!-- END FACTS -->\n"
            f"\n"
            f"Summarize the facts. Take care to preserve literal information."
        )

        response = LLMMethods.respond(prompt, list(), function_id="summarize", model="gpt-3.5-turbo")
        return response

    def naturalize(self, thought: str, tool_call: ToolCall) -> str:
        action = tool_call.tool_name
        arguments = tool_call.input
        observation = tool_call.output

        arguments_json = json.dumps(arguments)
        action_schema = self.toolbox.get_schema_from_name(action)
        fact = LLMMethods.naturalize(thought, action_schema, arguments_json, observation, model="gpt-3.5-turbo")
        return fact

    def implement_thought(self, thought: str, summary: str) -> ToolCall:
        try:
            docstring_dict = LLMMethods.openai_extract_arguments(thought, docstring_schema, strict=True, model="gpt-4-0613")

        except ExtractionException as e:
            raise ToolSelectionException("Error while extracting docstring.") from e

        docstring = compose_docstring(docstring_dict)
        tool_name = LLMMethods.select_tool_name(self.toolbox, docstring)
        if tool_name is not None:
            print(f"{colorama.Back.RED}Tool:{colorama.Style.RESET_ALL}")
            tool = self.toolbox.get_tool_from_name(tool_name)
            tool_schema = self.toolbox.get_schema_from_name(tool_name)
            arguments = LLMMethods.openai_extract_arguments(summary, tool_schema, model="gpt-3.5-turbo")
            tool_call = self.processor.apply_tool(tool, arguments, False)
            return tool_call

        tool_call = self.processor.apply_new_tool(summary, docstring_dict)
        return tool_call

    def _process_request(self, project_name: str, request: str, progress: dict[str, any], facts_db: hyperdb.HyperDB, history: list[dict[str, any]]) -> str:
        # "gpt-3.5-turbo-16k-0613", "gpt-4-32k-0613", "gpt-4-0613", "gpt-3.5-turbo-0613"

        last_action = ""
        last_step = "No step has been taken yet."

        while not progress["is_done"]:
            data_prompt = {"request": request, "last_step": last_step}
            prompt = (
                f"```json\n"
                f"{json.dumps(data_prompt, indent=4, sort_keys=True)}\n"
                f"```"
            )
            progress = LLMMethods.openai_extract_arguments(prompt, proceed, history=history, model="gpt-3.5-turbo-0613")
            if progress["is_done"]:
                break

            if 0 < len(last_action):
                self.toolbox.update_tool_stats(last_action, progress["was_last_action_effective"])

            thought = progress["thought"]
            print(
                f"{colorama.Back.RED}Thought:{colorama.Style.RESET_ALL}\n"
                f"{colorama.Fore.RED}{thought}{colorama.Style.RESET_ALL}"
            )

            if len(facts_db.documents) < 1:
                summary = (
                    f"{request}\n\n"
                    f"{thought}"
                )
            else:
                summary = self.summarize(facts_db, thought)

            tool_call = self.implement_thought(thought, summary)
            print(
                f"{colorama.Back.RED}Observation:{colorama.Style.RESET_ALL}\n"
                f"{colorama.Fore.RED}{tool_call.output}{colorama.Style.RESET_ALL}"
            )
            fact = self.naturalize(thought, tool_call)

            last_action = tool_call.tool_name
            self._save_project(project_name, request, progress, facts_db, fact, history)

        return progress["report"]
