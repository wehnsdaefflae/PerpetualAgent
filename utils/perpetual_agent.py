# coding=utf-8
import dataclasses
import json
import logging
import types
from traceback import format_exc

import colorama

from utils.basic_llm_calls import openai_chat
from utils.llm_methods import LLMMethods, ExtractionException, make_code_prompt
from utils.logging_handler import logging_handlers
from utils.misc import truncate, format_steps, extract_code_blocks
from utils.toolbox import ToolBox


class ToolCreationException(Exception):
    pass


class ToolApplicationException(Exception):
    pass


@dataclasses.dataclass
class ToolResult:
    result: str
    is_finalized: bool
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

    def _extract_arguments(self, state: str, tool_name: str) -> dict[str, any]:
        tool_schema = self.toolbox.get_schema_from_name(tool_name)
        arguments = LLMMethods.extract_arguments(state, tool_schema)
        return arguments

    def _make_code(self, message_history: list[dict[str, any]]) -> str:
        response = openai_chat("make_code", messages=message_history, model="gpt-4")
        message = response["choices"][0]["message"]
        content = message["content"]

        try:
            tool_code = extract_code_blocks(content)[0]
            _ = self.toolbox.get_name_from_code(tool_code)
            _ = self.toolbox.get_temp_tool_from_code(tool_code)
            _ = self.toolbox.get_schema_from_code(tool_code)
            _ = self.toolbox.get_description_from_code(tool_code)
            message_history.append(
                {"role": "assistant", "content": message}
            )
            return tool_code

        except Exception as e:
            self.logger.error(f"Error while extracting tool code: {e}")
            raise ToolCreationException("Error while extracting tool code.") from e

    def _confirmation(self, tool_name: str, arguments: dict[str, any]) -> bool:
        truncated_arguments = ", ".join(f"str({k})={truncate(str(v), 50)!r}" for k, v in arguments.items())
        tool_call = f"{tool_name}({truncated_arguments})"

        response = input(f"{tool_call}{colorama.Style.RESET_ALL} [y/N]: ")
        return "y" == response.lower().strip()

    def _apply_tool(self, state: str, tool: types.FunctionType, is_temp_tool: bool) -> ToolResult:
        tool_name = tool.__name__
        arguments = self._extract_arguments(state, tool_name)

        if not self._confirmation(tool_name, arguments):
            del tool
            return ToolResult("User rejected tool.", False, True)

        try:
            result = tool(**arguments)

        except Exception as e:
            result = f"Error while applying tool '{tool_name}': {e}"
            self.logger.error(result)
            if is_temp_tool:
                trace = format_exc()
                self.logger.error(trace)
                return ToolResult(trace, False, False)

        finally:
            del tool

        return ToolResult(result, tool_name == "finalize", True)

    def _apply_new_tool(self, state: str, docstring: str) -> ToolResult:
        tool_descriptions_string = self.toolbox.get_all_descriptions_string()
        code_prompt = make_code_prompt.format(tool_descriptions=tool_descriptions_string, docstring=docstring)
        message_history = [
            {"role": "user", "content": code_prompt}
        ]

        for _ in range(self.implementation_attempts):
            try:
                new_tool_code = self._make_code(message_history)

            except ToolCreationException as e:
                self.logger.error(e)
                return ToolResult(f"Tool creation failed. {e}", False, False)

            tmp_tool = self.toolbox.get_temp_tool_from_code(new_tool_code)
            tool_result = self._apply_tool(state, tmp_tool, True)
            if tool_result.succeeded:
                self.toolbox.save_tool_code(new_tool_code, False)
                return tool_result

            message_history.append(
                {"role": "user", "content": tool_result.result}
            )

        return ToolResult(f"Tool application failed permanently after {self.implementation_attempts} attempts.", False, False)

    def _condense_result(self, result: str, action_description: str) -> str:
        if len(result) > self.result_limit:
            result = LLMMethods.vector_summarize(action_description, result, model="gpt-3.5-turbo-0613")
        return result

    def pipeline(self, progress_summary: str, action_description: str) -> tuple[str, bool]:
        print(f"{colorama.Fore.CYAN}Summary: {progress_summary}")
        print(f"{colorama.Fore.YELLOW}Action: {action_description}")
        complete_state = progress_summary + "\n\n" + action_description
        docstring = LLMMethods.make_function_docstring(action_description, model="gpt-4")
        tool_description = self.toolbox.get_description_from_docstring(docstring)

        tool_name = LLMMethods.select_tool_name(self.toolbox, tool_description)
        if tool_name is None:
            print(f"{colorama.Fore.RED}{colorama.Style.BRIGHT}New tool: ", end="")
            tool_result = self._apply_new_tool(complete_state, docstring)
            print(f"{colorama.Style.RESET_ALL}", end="")

        else:
            print(f"{colorama.Fore.RED}Tool: ", end="")
            tool = self.toolbox.get_tool_from_name(tool_name)
            tool_result = self._apply_tool(progress_summary, tool, False)

        step_result = self._condense_result(tool_result.result, action_description)
        print(f"{colorama.Fore.BLUE}Result: {truncate(step_result, 200)}{colorama.Style.RESET_ALL}\n")
        return step_result, tool_result.is_finalized


class PerpetualAgent:
    def __init__(self) -> None:
        self.main_logger = logging.getLogger()
        self.main_logger.setLevel(logging.INFO)
        for each_handler in logging_handlers():
            self.main_logger.addHandler(each_handler)

        self.toolbox = ToolBox("tools/")
        self.processor = StepProcessor(self.toolbox)

    def _get_result_old(self, step_description: str, summary: str) -> tuple[str, bool]:
        print(f"  {colorama.Fore.GREEN}Command: {step_description}{colorama.Style.RESET_ALL}")

        docstring = LLMMethods.make_function_docstring(step_description, model="gpt-4")
        tool_description = self.toolbox.get_description_from_docstring(docstring)
        new_tool_code = None
        tool_name = LLMMethods.select_tool_name(self.toolbox, tool_description)

        each_attempt = 0
        max_attempts = 3

        code_prompt = make_code_prompt.format(tool_descriptions=self.toolbox.get_all_descriptions_string(), docstring=docstring)
        code_history = [{"role": "user", "content": code_prompt}]

        while True:
            # new tool
            if tool_name is None:
                print(f"{colorama.Fore.YELLOW}  New action:{colorama.Style.RESET_ALL}", end=" ")
                try:
                    response = openai_chat("make_code", code_history, model="gpt-4")
                    message = response["choices"][0]["message"]
                    code_history.append({"role": "assistant", "content": message})
                    content = message["content"]
                    new_tool_code = extract_code_blocks(content)[0]

                    tool_name = self.toolbox.get_name_from_code(new_tool_code)
                    tool = self.toolbox.get_temp_tool_from_code(new_tool_code)
                    schema = self.toolbox.get_schema_from_code(new_tool_code)
                    _description = self.toolbox.get_description_from_code(new_tool_code)

                except Exception as e:
                    exception_message = f"Tool creation failed, invalid code: {e}."
                    self.main_logger.error(exception_message)
                    return exception_message, False

            # existing tool
            else:
                print(f"{colorama.Fore.YELLOW}  Action:{colorama.Style.RESET_ALL}", end=" ")
                tool = self.toolbox.get_tool_from_name(tool_name)
                schema = self.toolbox.get_schema_from_name(tool_name)

            # extract arguments
            try:
                arguments = LLMMethods.extract_arguments(summary + "\n\n" + step_description, schema, model="gpt-3.5-turbo-0613")

            except ExtractionException as e:
                exception_message = format_exc()
                self.main_logger.error(exception_message)
                return f"Extraction of arguments failed: {exception_message}", False

            truncated_arguments = ", ".join(f"str({k})={truncate(str(v), 50)!r}" for k, v in arguments.items())
            tool_call = f"{tool_name}({truncated_arguments})"
            user_input = input(f"{colorama.Fore.YELLOW}{tool_call}{colorama.Style.RESET_ALL} [y/N]? ")
            if user_input != "y":
                return f"Action `{tool_call}` rejected by user.", False

            self.main_logger.info(f"Executing action `{tool_call}`.")

            # call tool
            try:
                result = tool(**arguments)
                del tool
                if tool_name == "finalize":
                    return result, True

                if new_tool_code is not None:
                    self.toolbox.save_tool_code(new_tool_code, False)

                result_json = json.dumps(result)
                return result_json, False

            except Exception as e:
                exception_message = format_exc()
                self.main_logger.error(exception_message)
                if new_tool_code is None:
                    return f"Execution of action failed: {e}", False

                elif each_attempt >= max_attempts:
                    return f"Tool creation failed, cannot be applied: {e}", False

                code_history.append({"role": "user", "content": exception_message})
                each_attempt += 1
                self.main_logger.info(f"Tool creation failed at attempt {each_attempt}: {e}.")

    def respond(self, main_request: str) -> str:
        improved_request = LLMMethods.improve_request(main_request, model="gpt-3.5-turbo")

        print(f"{colorama.Fore.CYAN}{improved_request}{colorama.Style.RESET_ALL}\n")

        summary_length_limit = 5_000

        i = 1
        summary = ""
        while True:
            # "gpt-3.5-turbo-16k-0613", "gpt-4-32k-0613", "gpt-4-0613", "gpt-3.5-turbo-0613"
            step_description = LLMMethods.sample_next_step_from_summary(improved_request, summary, model="gpt-3.5-turbo")
            self.main_logger.info(step_description)

            output_step = f"Step {i}:"
            print(output_step)

            result, is_finalized = self.processor.pipeline(summary, step_description)

            print("====================================\n")

            if is_finalized:
                self.main_logger.info("Request fulfilled.")
                print("Request fulfilled.")
                return result

            if len(summary) >= summary_length_limit:
                summary = LLMMethods.summarize(summary, instruction="Summarize the actions and results from the text above.", model="gpt-3.5-turbo")

            this_step = [
                {"role": "user", "content": step_description},
                {"role": "assistant", "content": result}
            ]
            formatted_step = format_steps(this_step)
            summary += "\n" + formatted_step

            summary_output = f"{colorama.Fore.RED}  Summary: {summary}{colorama.Style.RESET_ALL}"
            print(summary_output)
            self.main_logger.info(summary)

            i += 1
