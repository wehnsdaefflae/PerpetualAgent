# coding=utf-8
import json
import logging
from traceback import format_exc

import colorama

from utils.basic_llm_calls import openai_chat
from utils.llm_methods import LLMMethods, ExtractionException, make_code_prompt
from utils.logging_handler import logging_handlers
from utils.misc import truncate, format_steps
from utils.toolbox import ToolBox


class ToolCreationException(Exception):
    pass


class ToolApplicationException(Exception):
    pass


class PerpetualAgent:
    def __init__(self) -> None:
        self.toolbox = ToolBox("tools/")
        self.main_logger = logging.getLogger()
        self.main_logger.setLevel(logging.INFO)
        for each_handler in logging_handlers():
            self.main_logger.addHandler(each_handler)

    def _get_result(self, step_description: str, summary: str) -> tuple[str, bool]:
        print(f"  {colorama.Fore.GREEN}Command: {step_description}{colorama.Style.RESET_ALL}")

        docstring = LLMMethods.make_function_docstring(step_description, model="gpt-4")
        new_tool_code = None
        tool_name = LLMMethods.select_tool_name(self.toolbox, docstring)

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
                    new_tool_code = message["content"]

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

        result_length_limit = 2_000
        summary_length_limit = 5_000

        i = 1
        summary = ""
        while True:
            # step_description = LLMMethods.sample_next_step(improved_request, previous_steps, model="gpt-4", temperature=.2)
            # step_description = LLMMethods.sample_next_step(improved_request, previous_steps, model="gpt-3.5-turbo", temperature=.0)
            step_description = LLMMethods.sample_next_step_from_summary(improved_request, summary, model="gpt-3.5-turbo")
            # step_description = LLMMethods._sample_next_step(improved_request, previous_steps, model="gpt-3.5-turbo", temperature=.0)
            self.main_logger.info(step_description)

            output_step = f"Step {i}:"
            print(output_step)

            # MESSAGE HISTORY = [{"role": "assistant", "content": <last_code>}, {"role": "user", "content": <last_error>}] try 3 times?
            result, is_finalized = self._get_result(step_description, summary)
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

            # "model": "gpt-3.5-turbo-16k-0613"
            # "model": "gpt-4-32k-0613"
            # "model": "gpt-4-0613"
            # "model": "gpt-3.5-turbo-0613"

            i += 1
