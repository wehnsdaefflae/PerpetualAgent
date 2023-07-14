# coding=utf-8
import dataclasses
import logging
import types
from traceback import format_exc

import colorama

from utils.basic_llm_calls import openai_chat
from utils.llm_methods import LLMMethods
from utils.prompts import CODER, STEP_SUMMARIZER
from utils.logging_handler import logging_handlers
from utils.misc import truncate, extract_code_blocks, insert_docstring
from utils.prompts import PROGRESS_UPDATER, PROGRESS_REPORT
from utils.toolbox import ToolBox


class ToolCreationException(Exception):
    pass


class ToolApplicationException(Exception):
    pass


@dataclasses.dataclass
class ToolResult:
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

    def _make_code(self, message_history: list[dict[str, any]], docstring: str) -> str:
        response = openai_chat("make_code", messages=message_history, model="gpt-4")
        message = response["choices"][0]["message"]
        content = message["content"]

        try:
            tool_code = extract_code_blocks(content)[0]
            tool_code = insert_docstring(tool_code, docstring)
            _ = self.toolbox.get_name_from_code(tool_code)
            _ = self.toolbox.get_temp_tool_from_code(tool_code)
            _ = self.toolbox.get_schema_from_code(tool_code)
            _ = self.toolbox.get_description_from_code(tool_code)
            message_history.append(
                {"role": "assistant", "content": f"```python\n{tool_code}\n```"}
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

    def _apply_tool(self, tool: types.FunctionType, arguments: dict[str, any], is_temp_tool: bool) -> ToolResult:
        tool_name = tool.__name__

        if not self._confirmation(tool_name, arguments):
            del tool
            return ToolResult("User rejected tool.", True)

        try:
            result = tool(**arguments)

        except Exception as e:
            result = f"Error while applying tool '{tool_name}': {e}"
            self.logger.error(result)
            if is_temp_tool:
                trace = format_exc()
                self.logger.error(trace)
                return ToolResult(trace, False)

        finally:
            del tool

        return ToolResult(str(result), True)

    def _apply_new_tool(self, text: str, docstring: str) -> str:
        tool_descriptions_string = self.toolbox.get_all_descriptions_string()
        code_prompt = CODER.format(tool_descriptions=tool_descriptions_string, docstring=docstring)
        message_history = [
            {"role": "user", "content": code_prompt}
        ]

        for _ in range(self.implementation_attempts):
            try:
                new_tool_code = self._make_code(message_history, docstring)

            except ToolCreationException as e:
                self.logger.error(e)
                print(colorama.Style.RESET_ALL)
                return f"Tool creation failed. {e.__cause__ if e.__cause__ else e}"

            tmp_tool = self.toolbox.get_temp_tool_from_code(new_tool_code)
            tool_schema = self.toolbox.get_schema_from_code(new_tool_code)
            arguments = LLMMethods.openai_extract_arguments(text, tool_schema, model="gpt-3.5-turbo-0613")
            tool_result = self._apply_tool(tmp_tool, arguments, True)
            if tool_result.succeeded:
                self.toolbox.save_tool_code(new_tool_code, False)
                return tool_result.result

            message_history.append(
                {"role": "user", "content": tool_result.result}
            )

        return f"Tool application failed permanently after {self.implementation_attempts} attempts."

    def _condense_result(self, result: str, request: str) -> str:
        if len(result) > self.result_limit:
            result = LLMMethods.vector_summarize(request, result, model="gpt-3.5-turbo")
        return result

    def perform(self, action: str, progress_report: str) -> str:
        try:
            docstring = LLMMethods.make_function_docstring(action, model="gpt-4-0613")
        except Exception as e:
            return f"Action description failed. {e}"

        tool_name = LLMMethods.select_tool_name(self.toolbox, docstring)
        if tool_name is None:
            print(f"{colorama.Fore.BLACK}{colorama.Back.RED}{colorama.Style.BRIGHT}New tool: ", end="")
            tool_result = self._apply_new_tool(progress_report, docstring)

        else:
            print(f"{colorama.Fore.RED}Tool: ", end="")
            tool = self.toolbox.get_tool_from_name(tool_name)
            tool_schema = self.toolbox.get_schema_from_name(tool_name)
            arguments = LLMMethods.extract_arguments(progress_report, tool_schema, model="gpt-3.5-turbo")
            tool_output = self._apply_tool(tool, arguments, False)
            tool_result = tool_output.result

        step_result = self._condense_result(tool_result, action)
        return step_result


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
        progress = "[no steps performed yet]"
        last_progress = "[no progress yet]"
        last_action = "[no action yet]"
        last_result = "[no result yet]"
        while True:
            # "gpt-3.5-turbo-16k-0613", "gpt-4-32k-0613", "gpt-4-0613", "gpt-3.5-turbo-0613"

            output_step = f"Step {i}:"
            print(output_step)

            if i < 2:
                print(f"{colorama.Fore.CYAN}First step.")
                summary = (
                    f"## Request\n"
                    f"{improved_request.strip()}"
                )
                action = LLMMethods.sample_first_action(improved_request, model="gpt-3.5-turbo")

            else:
                print(f"{colorama.Fore.CYAN}Progress: {progress.strip()}")
                summary = PROGRESS_REPORT.format(
                    request=improved_request.strip(),
                    progress=last_progress.strip(),
                    action=last_action.strip(),
                    result=last_result.strip(),
                )

                action = LLMMethods.sample_next_action(summary, model="gpt-4")

            self.main_logger.info(action)
            print(f"{colorama.Fore.YELLOW}Action: {action.strip()}")

            if "[finalize]" in action.lower():
                self.main_logger.info(f"Request fulfilled: {progress}")
                print(colorama.Style.RESET_ALL)
                return progress

            result = self.processor.perform(action, summary)  # literal action description
            print(f"{colorama.Fore.BLUE}Result: {truncate(result, 200)}{colorama.Style.RESET_ALL}\n")

            print("====================================\n")

            if i < 2:
                update_progress_prompt = STEP_SUMMARIZER.format(
                    request=improved_request.strip(),
                    action=action.strip(),
                    result=result.strip())

            else:
                update_progress_prompt = PROGRESS_UPDATER.format(
                    request=improved_request.strip(),
                    progress=progress.strip(),
                    action=action.strip(),
                    result=result.strip())

            last_progress = progress

            progress = LLMMethods.respond(update_progress_prompt, list(), function_id="summarize", model="gpt-3.5-turbo")
            self.main_logger.info(progress)

            last_action = action
            last_result = result

            i += 1
