# coding=utf-8
import json
import logging
from traceback import format_exc

import colorama

from utils.llm_methods import LLMMethods, ExtractionException
from utils.logging_handler import logging_handlers
from utils.misc import truncate, format_steps
from utils.toolbox import ToolBox


class PerpetualAgent:
    def __init__(self) -> None:
        self.toolbox = ToolBox("tools/")
        self.main_logger = logging.getLogger()
        self.main_logger.setLevel(logging.INFO)
        for each_handler in logging_handlers():
            self.main_logger.addHandler(each_handler)

    def _get_result_summary(self, step_description: str, summary: str) -> tuple[str, bool]:
        print(f"  {colorama.Fore.GREEN}Command: {step_description}{colorama.Style.RESET_ALL}")

        docstring = LLMMethods.make_function_docstring(step_description, model="gpt-4")
        new_tool_code = None
        tool_name = LLMMethods.select_tool_name(self.toolbox, docstring)

        # take tool_arguments or function_description
        if tool_name is None:
            print(f"{colorama.Fore.YELLOW}  New action:{colorama.Style.RESET_ALL}", end=" ")
            try:
                new_tool_code = LLMMethods.make_code(self.toolbox, docstring, message_history=None, model="gpt-4")

                tool_name = self.toolbox.get_name_from_code(new_tool_code)
                tool = self.toolbox.get_temp_tool_from_code(new_tool_code)
                schema = self.toolbox.get_schema_from_code(new_tool_code)

            except Exception as e:
                print()
                exception_message = format_exc()
                self.main_logger.error(exception_message)
                return f"Creation of action failed: {exception_message}", False

        else:
            print(f"{colorama.Fore.YELLOW}  Action:{colorama.Style.RESET_ALL}", end=" ")
            tool = self.toolbox.get_tool_from_name(tool_name)
            schema = self.toolbox.get_schema_from_name(tool_name)

        try:
            # todo: why previous steps?!
            arguments = LLMMethods.extract_arguments(list(), schema, step_description, model="gpt-3.5-turbo-0613")

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

        try:
            result = tool(**arguments)
            del tool
            if tool_name == "finalize":
                return result, True

            if new_tool_code is not None:
                self.toolbox.save_tool_code(new_tool_code, False)

        except Exception as e:
            exception_message = format_exc()
            self.main_logger.error(exception_message)
            return f"Execution of action failed: {exception_message}", False

        result_json = json.dumps(result)
        return result_json, False

    def _get_result(self, step_description: str, previous_steps: list[dict[str, str]]) -> tuple[str, bool]:
        print(f"  {colorama.Fore.GREEN}Command: {step_description}{colorama.Style.RESET_ALL}")

        docstring = LLMMethods.make_function_docstring(step_description, model="gpt-4")
        new_tool_code = None
        tool_name = LLMMethods.select_tool_name(self.toolbox, docstring)

        # take tool_arguments or function_description
        if tool_name is None:
            print(f"{colorama.Fore.YELLOW}  New action:{colorama.Style.RESET_ALL}", end=" ")
            try:
                new_tool_code = LLMMethods.make_code(self.toolbox, docstring, message_history=previous_steps, model="gpt-4")

                tool_name = self.toolbox.get_name_from_code(new_tool_code)
                tool = self.toolbox.get_temp_tool_from_code(new_tool_code)
                schema = self.toolbox.get_schema_from_code(new_tool_code)

            except Exception as e:
                print()
                exception_message = format_exc()
                self.main_logger.error(exception_message)
                return f"Creation of action failed: {exception_message}", False

        else:
            print(f"{colorama.Fore.YELLOW}  Action:{colorama.Style.RESET_ALL}", end=" ")
            tool = self.toolbox.get_tool_from_name(tool_name)
            schema = self.toolbox.get_schema_from_name(tool_name)

        try:
            # todo: why previous steps?!
            arguments = LLMMethods.extract_arguments(previous_steps, schema, step_description, model="gpt-3.5-turbo-0613")

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

        try:
            result = tool(**arguments)
            del tool
            if tool_name == "finalize":
                return result, True

            if new_tool_code is not None:
                self.toolbox.save_tool_code(new_tool_code, False)

        except Exception as e:
            exception_message = format_exc()
            self.main_logger.error(exception_message)
            return f"Execution of action failed: {exception_message}", False

        result_json = json.dumps(result)
        return result_json, False

    def respond(self, main_request: str, step_memory: int = 100) -> str:
        improved_request = LLMMethods.improve_request(main_request, model="gpt-3.5-turbo")

        print(f"{colorama.Fore.CYAN}{improved_request}{colorama.Style.RESET_ALL}\n")

        result_length_limit = 2_000
        summary_length_limit = 5_000

        i = 1
        previous_steps = list()
        summary = ""
        while True:
            # step_description = LLMMethods.sample_next_step(improved_request, previous_steps, model="gpt-4", temperature=.2)
            # step_description = LLMMethods.sample_next_step(improved_request, previous_steps, model="gpt-3.5-turbo", temperature=.0)
            step_description = LLMMethods.sample_next_step_from_summary(improved_request, summary, model="gpt-3.5-turbo")
            # step_description = LLMMethods._sample_next_step(improved_request, previous_steps, model="gpt-3.5-turbo", temperature=.0)
            self.main_logger.info(step_description)

            output_step = f"Step {i}:"
            print(output_step)

            result, is_finalized = self._get_result(step_description, previous_steps)
            if len(result) > result_length_limit:
                result = LLMMethods.vector_summarize(step_description, result, model="gpt-3.5-turbo-0613")
                output_result = f"{colorama.Fore.BLUE}  Summarized result: {result}{colorama.Style.RESET_ALL}"
            else:
                output_result = f"{colorama.Fore.BLUE}  Result: {result}{colorama.Style.RESET_ALL}"

            print(output_result)
            self.main_logger.info(result)
            print("====================================\n")

            if is_finalized:
                self.main_logger.info("Request fulfilled.")
                print("Request fulfilled.")
                return result

            this_step = [
                {"role": "user", "content": step_description},
                {"role": "assistant", "content": result}
            ]
            formatted_step = format_steps(this_step)
            summary += "\n" + formatted_step
            if len(summary) >= summary_length_limit:
                summary = LLMMethods.summarize(summary, instruction="Summarize the actions and results from the text above.", model="gpt-3.5-turbo")
            previous_steps.extend(this_step)

            summary_output = f"{colorama.Fore.RED}  Summary: {summary}{colorama.Style.RESET_ALL}"
            print(summary_output)
            self.main_logger.info(summary)

            # "model": "gpt-3.5-turbo-16k-0613"
            # "model": "gpt-4-32k-0613"
            # "model": "gpt-4-0613"
            # "model": "gpt-3.5-turbo-0613"

            del previous_steps[:-step_memory]
            i += 1
