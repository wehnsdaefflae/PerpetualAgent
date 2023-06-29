# coding=utf-8
import json
import logging
import colorama

from utils.llm_methods import LLMMethods, ExtractionException
from utils.logging_handler import logging_handlers
from utils.misc import truncate
from utils.toolbox import ToolBox


class PerpetualAgent:
    def __init__(self) -> None:
        self.toolbox = ToolBox("tools/")
        self.main_logger = logging.getLogger()
        self.main_logger.setLevel(logging.INFO)
        for each_handler in logging_handlers():
            self.main_logger.addHandler(each_handler)

    def improve_request(self, main_request: str, *parameters: any, **kwargs: any) -> str:
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
                  f"Respond only with the improved version of the request. Make it concise and to the point. Do not exceed five sentences, do not use bullet points, "
                  f"do not address the points above explicitly, do not include any of the above points in your response, and do not encourage checking back. They're on "
                  f"their own on this one.\n")
        # improved_request = LLMMethods.respond(prompt, list(), *parameters, **kwargs)
        improved_request = LLMMethods.respond(prompt, list(), *parameters, **kwargs)
        return improved_request

    def _get_result(self, step_description: str, previous_steps: list[dict[str, str]]) -> tuple[str, bool]:
        function_description = LLMMethods.describe_function(step_description, model="gpt-4")
        new_tool_code = None
        tool_name = LLMMethods.select_tool_name(self.toolbox, function_description)

        # take tool_arguments or function_description
        if tool_name is None:
            try:
                new_tool_code = LLMMethods.make_tool_code(self.toolbox, function_description, message_history=previous_steps, model="gpt-4")
                tool_name = self.toolbox.get_name_from_code(new_tool_code)
                tool = self.toolbox.get_temp_tool_from_code(new_tool_code)
                schema = self.toolbox.get_schema_from_code(new_tool_code)

            except Exception as e:
                creation_error = f"Creation of action failed: {e}"
                self.main_logger.error(creation_error)
                return creation_error, False

        else:
            tool = self.toolbox.get_tool_from_name(tool_name)
            schema = self.toolbox.get_schema_from_name(tool_name)

        try:
            arguments = LLMMethods.extract_arguments(previous_steps, schema, step_description, model="gpt-3.5-turbo-0613")

        except ExtractionException as e:
            extraction_error = f"Extraction of arguments failed: {e}"
            self.main_logger.error(extraction_error)
            return extraction_error, False

        new_str = "" if new_tool_code is None else " (new)"
        truncated_arguments = ", ".join(f"str({k})={truncate(str(v), 50)!r}" for k, v in arguments.items())
        tool_call = f"{tool_name}({truncated_arguments})"
        user_input = input(f"{colorama.Fore.YELLOW}  Action{new_str}: {tool_call} [y/N]? {colorama.Style.RESET_ALL}")
        if user_input != "y":
            reject = f"Action `{tool_call}` rejected by user."
            self.main_logger.info(reject)
            return reject, False

        self.main_logger.info(f"Executing action `{tool_call}`.")

        try:
            result = tool(**arguments)
            del tool
            if tool_name == "finalize":
                return result, True

            if new_tool_code is not None:
                self.toolbox.save_tool_code(new_tool_code, False)

        except Exception as e:
            execution_error = f"Execution of action failed: {e}"
            self.main_logger.error(execution_error)
            return execution_error, False

        arguments_json = json.dumps(arguments)
        result_json = json.dumps(result)
        result_naturalized = LLMMethods.naturalize(step_description, schema, arguments_json, result_json, model="gpt-3.5-turbo-0613")
        return result_naturalized, False

    def respond(self, main_request: str, step_memory: int = 100) -> str:
        improved_request = self.improve_request(main_request, model="gpt-3.5-turbo")

        print(f"{colorama.Fore.CYAN}{improved_request}{colorama.Style.RESET_ALL}\n")

        i = 1
        previous_steps = list()
        intermediate_results = list()
        while True:
            """
            extracted_info = LLMMethods.extract_arguments(previous_steps, extract_next_step, prompt=improved_request, model="gpt-4-0613", temperature=.2)
            step_description = extracted_info["next_step"]
            if extracted_info["is_done"]:
                self.main_logger.info("Request fulfilled.")
                break
            """
            # step_description = LLMMethods.sample_next_step(improved_request, previous_steps, model="gpt-4", temperature=.2)
            step_description = LLMMethods.sample_next_step(improved_request, previous_steps, model="gpt-3.5-turbo", temperature=.0)
            # step_description = LLMMethods._sample_next_step(improved_request, previous_steps, model="gpt-3.5-turbo", temperature=.0)

            output_step = f"Step {i}:\n  {step_description}"
            print(f"{colorama.Fore.GREEN}{output_step}{colorama.Style.RESET_ALL}")
            self.main_logger.info(output_step)

            result, is_finalized = self._get_result(step_description, previous_steps)
            if is_finalized:
                self.main_logger.info("Request fulfilled.")
                final_response = f"Final response:\n{result}"
                return final_response

            output_step = f"Result: {result}"
            print(f"{colorama.Fore.BLUE}  {output_step}{colorama.Style.RESET_ALL}\n====================================\n")
            self.main_logger.info(output_step)

            intermediate_results.append(result)
            this_step = [
                {"role": "user", "content": step_description},
                {"role": "assistant", "content": truncate(result, 1_000, at_start=True)}
            ]
            previous_steps.extend(this_step)

            # "model": "gpt-3.5-turbo-16k-0613"
            # "model": "gpt-4-32k-0613"
            # "model": "gpt-4-0613"
            # "model": "gpt-3.5-turbo-0613"

            del previous_steps[:-step_memory]
            i += 1
