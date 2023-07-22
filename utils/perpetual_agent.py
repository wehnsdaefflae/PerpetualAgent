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
from utils.json_schemata import docstring_schema, progress_schema, update_progress
from utils.llm_methods import LLMMethods, ExtractionException
from utils.prompts import CODER
from utils.logging_handler import logging_handlers
from utils.misc import truncate, extract_code_blocks, insert_docstring, compose_docstring, get_date_name
from utils.prompts import PROGRESS_REPORT
from utils.toolbox import ToolBox, SchemaExtractionException


class ToolCreationException(Exception):
    def __init__(self, message: str, data: dict[str, any] | None = None) -> None:
        super().__init__(message)
        self.data = data or dict()


class ToolApplicationException(Exception):
    def __init__(self, data: dict[str, any]) -> None:
        self.data = data
        super().__init__()


@dataclasses.dataclass
class ToolResult:
    tool_call: str
    result: str
    succeeded: bool


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

    def _apply_tool(self, tool: types.FunctionType, arguments: dict[str, any], is_temp_tool: bool) -> ToolResult:
        tool_name = tool.__name__

        truncated_arguments = ", ".join(f"str({k})={truncate(str(v), 50)!r}" for k, v in arguments.items())
        tool_call = f"{tool_name}({truncated_arguments})"

        if not self._confirmation(tool_call):
            del tool
            return ToolResult(tool_call, "User rejected execution.", False)

        try:
            result = tool(**arguments)

        except Exception as e:
            result = f"{tool_call}: Error during execution. {e}"
            self.logger.error(result)
            if is_temp_tool:
                trace = format_exc()
                self.logger.error(trace)
                return ToolResult(tool_call, str(trace), False)

        finally:
            del tool

        return ToolResult(tool_call, str(result), True)

    def _apply_new_tool(self, text: str, docstring_dict: dict[str, any]) -> ToolResult:
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
                return ToolResult("[tool_creation_failed]", f"{e.__cause__ if e.__cause__ else e}", False)

            try:
                tool_schema = self.toolbox.get_schema_from_code(new_tool_code, docstring_dict)

            except SchemaExtractionException as e:
                self.logger.error(e)
                return ToolResult("[schema_extraction_failed]", f"{e}", False)

            try:
                arguments = LLMMethods.openai_extract_arguments(text, tool_schema, model="gpt-3.5-turbo-0613")

            except ExtractionException as e:
                self.logger.error(e)
                return ToolResult("[argument_extraction_failed]", f"{e.__cause__ if e.__cause__ else e}", False)

            tool_result = self._apply_tool(tmp_tool, arguments, True)
            if tool_result.succeeded:
                self.toolbox.save_tool_code(new_tool_code, docstring_dict, False)
                return tool_result

            message_history.append(
                {"role": "user", "content": tool_result.result}
            )

        return ToolResult("[tool_execution_failed_permanently]", f"Execution failed after {self.implementation_attempts} attempts.", False)

    def _condense_result(self, result: str, request: str) -> str:
        if len(result) > self.result_limit:
            result = LLMMethods.vector_summarize(request, result, model="gpt-3.5-turbo")
        return result

    def perform(self, action: str, progress_report: str) -> ToolResult:
        try:
            docstring_dict = LLMMethods.openai_extract_arguments(action, docstring_schema, strict=True, model="gpt-4-0613")
        except Exception as e:
            return ToolResult("[action_selection_failed]", f"{e}", False)

        docstring = compose_docstring(docstring_dict)
        tool_name = LLMMethods.select_tool_name(self.toolbox, docstring)
        if tool_name is None:
            print(f"{colorama.Back.RED}{colorama.Style.BRIGHT}New tool:{colorama.Style.RESET_ALL}")
            tool_result = self._apply_new_tool(progress_report, docstring_dict)

        else:
            print(f"{colorama.Back.RED}Tool:{colorama.Style.RESET_ALL}")
            tool = self.toolbox.get_tool_from_name(tool_name)
            tool_schema = self.toolbox.get_schema_from_name(tool_name)
            arguments = LLMMethods.openai_extract_arguments(progress_report, tool_schema, model="gpt-3.5-turbo")
            tool_result = self._apply_tool(tool, arguments, False)

        step_result = self._condense_result(tool_result.result, action)
        return ToolResult(tool_result.tool_call, step_result, True)


class PerpetualAgent:
    def __init__(self) -> None:
        self.main_logger = logging.getLogger()
        self.main_logger.setLevel(logging.INFO)
        for each_handler in logging_handlers():
            self.main_logger.addHandler(each_handler)

        self.toolbox = ToolBox("tools/")
        self.processor = StepProcessor(self.toolbox)

    def respond(self, main_request: str) -> str:
        improved_request = LLMMethods.improve_request(main_request, model="gpt-3.5-turbo")

        print(f"{colorama.Fore.CYAN}{improved_request}{colorama.Style.RESET_ALL}\n")

        summary_length_limit = 5_000

        i = 1
        last_progress = "[no progress yet]"
        last_tool_call = "[no action yet]"
        last_tool_result = "[no result yet]"
        while True:
            # "gpt-3.5-turbo-16k-0613", "gpt-4-32k-0613", "gpt-4-0613", "gpt-3.5-turbo-0613"

            print(f"Step {i}:\n")

            print(
                f"{colorama.Back.CYAN}Progress:{colorama.Style.RESET_ALL}\n"
                f"{colorama.Fore.CYAN}{last_progress.strip()}{colorama.Style.RESET_ALL}\n"
            )

            summary = PROGRESS_REPORT.format(
                request=improved_request.strip(),
                progress=last_progress.strip(),
                action=last_tool_call.strip(),
                result=last_tool_result.strip(),
            )

            if i < 2:
                action = LLMMethods.sample_first_action(summary, model="gpt-3.5-turbo")
            else:
                action = LLMMethods.sample_next_action(summary, model="gpt-3.5-turbo")

            self.main_logger.info(action)
            print(
                f"{colorama.Back.YELLOW}Action:{colorama.Style.RESET_ALL}\n"
                f"{colorama.Fore.YELLOW}{action}{colorama.Style.RESET_ALL}\n"
            )

            if "[finalize]" in action.lower():
                self.main_logger.info(f"Request fulfilled: {last_progress}")
                return last_progress

            tool_result = self.processor.perform(action, summary)  # literal action description
            print(
                f"{colorama.Back.BLUE}Result ({'succeeded' if tool_result.succeeded else 'failed'}):{colorama.Style.RESET_ALL}\n"
                f"{colorama.Fore.BLUE}{truncate(tool_result.result, 200)}{colorama.Style.RESET_ALL}\n"
            )

            print("====================================\n")

            """
            update_progress_prompt = PROGRESS_UPDATER.format(PROGRESS_REPORT=summary)
            last_progress = LLMMethods.respond(update_progress_prompt, list(), function_id="update_progress", model="gpt-3.5-turbo")
            """

            last_progress_dict = LLMMethods.openai_extract_arguments(summary, progress_schema)
            last_progress = last_progress_dict["updated_progress"]
            if i >= 2:
                last_tool_was_effective = last_progress_dict["was_last_action_effective"]
                self.toolbox.update_tool_stats(last_tool_call, last_tool_was_effective)

            last_tool_call = tool_result.tool_call
            last_tool_result = tool_result.result

            i += 1

    def respond_new(self, request: str, project_name: str | None = None) -> str:
        fact_db, progress = self.read_project_data(project_name)

        while not progress["is_done"]:
            report = progress["report"]
            thought = self.sample_next_thought(request, report)
            summary = self.summarize(fact_db, thought)
            action, arguments, observation = self.implement_thought(thought, summary)
            fact = self.naturalize(thought, action, arguments, observation)
            self.append_to_history(project_name, fact_db, fact)
            progress = self.update_progress(report, fact, request)
            # update action set. remove actions that frequently failed. add stats in `implement_thought`

        return progress["report"]

    def sample_next_thought(self, request: str, report: str) -> str:
        prompt = (
            f"<!-- BEGIN REQUEST -->\n"
            f"{request}\n"
            f"<!-- END REQUEST -->\n"
            f"\n"
            f"<!-- BEGIN PROGRESS REPORT -->\n"
            f"{report}\n"
            f"<!-- END PROGRESS REPORT -->\n"
            f"\n"
            f"Given the provided progress report, what would be an expert's next thought on how to fulfill the above request?"
        )
        response = LLMMethods.respond(prompt, list(), function_id="sample_next_thought", model="gpt-3.5-turbo")
        return response

    def summarize(self, history: hyperdb.HyperDB(), thought: str, n: int = 5) -> str:
        embedding, = get_embeddings([thought])
        no_documents = len(history.documents)
        document_indices, fitnesses = hyper_SVM_ranking_algorithm_sort(
            history.vectors,
            numpy.array(embedding),
            top_k=no_documents,
            metric=history.similarity_metric
        )

        new_fitness = list()
        for each_index, each_fitness in zip(document_indices, fitnesses):
            each_document = history.documents[each_index]
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
            f"Summarize the facts. Take care to preserve all literal information."
        )

        response = LLMMethods.respond(prompt, list(), function_id="summarize", model="gpt-3.5-turbo")
        return response

    def naturalize(self, thought: str, action: str, arguments: dict[str, any], observation: str) -> str:
        arguments_json = json.dumps(arguments)
        action_schema = self.toolbox.get_schema_from_name(action)
        fact = LLMMethods.naturalize(thought, action_schema, arguments_json, observation, model="gpt-3.5-turbo")
        return fact

    def update_progress(self, report: str, fact: str, request: str) -> dict[str, any]:
        prompt = (
            f"<!-- BEGIN REPORT -->\n"
            f"{report}\n"
            f"<!-- END REPORT -->\n"
            f"\n"
            f"<!-- BEGIN LAST FACT -->\n"
            f"{fact}\n"
            f"<!-- END LAST FACT -->\n"
            f"\n"
            f"<!-- BEGIN REQUEST -->\n"
            f"{request}\n"
            f"<!-- END REQUEST -->"
        )
        progress_report = LLMMethods.openai_extract_arguments(prompt, update_progress)
        return progress_report

    def implement_thought(self, thought: str, summary: str) -> tuple[str, dict[str, any], str]:
        try:
            # includes tool_name, args (done if tool_name == "finalize")
            action, arguments = self.get_action(thought, summary)

        except ToolCreationException as e:
            return "create_tool", e.data, f"{e.__cause__ if e.__cause__ else e}"

        try:
            # selection and execution must be combined to be able to repeat if creation or execution fails
            observation = self.perform_action(action, arguments)

        except ToolApplicationException as e:
            return f"apply_tool", e.data, f"{e.__cause__ if e.__cause__ else e}"

        return action, arguments, observation

    def get_action(self, thought: str, summary: str) -> tuple[str, dict[str, any]]:
        # given the thought and the summary, what is the next action to take?
        # 1. generate the docstring for a function that implements the thought
        # 2. search in the toolbox for a tool that matches the docstring
        # 3. if no tool is found, create a new tool (check it. if it fails, raise ToolCreationException(data={"docstring": docstring}))
        raise NotImplementedError()

    def perform_action(self, action: str, arguments: dict[str, any]) -> str:
        # perform the action with the given arguments and return the observation
        raise NotImplementedError()

    def append_to_history(self, project_name: str, history: hyperdb.HyperDB(), fact: str) -> None:
        embedding, = get_embeddings([fact])
        no_facts = len(history.documents)
        fact_json = json.dumps(
            {"fact": fact, "index": no_facts}
        )
        history.add_document(fact_json, embedding)
        history.save("facts_db.pickle.gz")
        project_directory = os.path.join("projects/", project_name)
        history_path = os.path.join(project_directory, "history.json")
        with open(history_path, mode="a") as file:
            json.dump(fact, file)
            file.write("\n")

    def read_project_data(self, project_name: str | None) -> tuple[hyperdb.HyperDB(), dict[str, any]]:
        project_directory = os.path.join("projects/", project_name)
        db = hyperdb.HyperDB()

        if project_name is None:
            project_name = get_date_name()
            self.main_logger.info(f"Starting new project '{project_name}'.")
            os.makedirs(project_directory)
            return db, {"report": "No progress yet.", "done": False}

        db.load("facts_db.pickle.gz")
        self.main_logger.info(f"Continuing project '{project_name}'.")
        progress = self.read_progress(project_directory)
        return db, progress

    def read_progress(self, project_directory: str) -> dict[str, any]:
        progress_path = os.path.join(project_directory, "progress.json")
        with open(progress_path, mode="r") as file:
            progress = json.load(file)
            assert isinstance(progress, dict)
        return progress
