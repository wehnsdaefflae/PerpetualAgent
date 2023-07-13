# coding=utf-8
import ast
import dataclasses
import re

import logging

from utils.logging_handler import logging_handlers

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handlers = logging_handlers()
for each_handler in handlers:
    logger.addHandler(each_handler)


def truncate(string: str, limit: int, indicator: str = "[...]", at_start: bool = False) -> str:
    if limit >= len(string):
        return string

    if at_start:
        return indicator + string[len(string) - limit:]

    return string[:limit - len(indicator)] + indicator


class DocstringException(Exception):
    pass


def extract_docstring(text: str) -> str:
    """
    This function extracts all the triple quoted strings from the given text.

    Parameters:
    text (str): The input string from which triple quoted strings need to be extracted.

    Returns:
    List[str]: A list of all triple quoted strings including the triple quotes.
    """

    # The pattern for triple quoted strings.
    double_quote_pattern = r'\"\"\"(.*?)\"\"\"'
    single_quote_pattern = r"\'\'\'(.*?)\'\'\'"
    all_quote_pattern = f"{double_quote_pattern}|{single_quote_pattern}"

    # Find all the matches for the pattern and flatten the result.
    matches = re.findall(all_quote_pattern, text, re.DOTALL)
    for double_quoted, single_quoted in matches:
        if double_quoted:
            return double_quoted
        if single_quoted:
            return single_quoted

    raise DocstringException()


def format_steps(message_history: list[dict[str, str]]) -> str:
    previous_steps = list()
    for i in range(0, len(message_history[-10:]), 2):
        each_request_message, each_response_message = message_history[i:i + 2]
        assert each_request_message["role"] == "user"
        assert each_response_message["role"] == "assistant"

        each_request = each_request_message["content"]
        each_response = each_response_message["content"]

        each_step = (
            f"STEP:\n"
            f"  ACTION: {each_request.strip()}\n"
            f"  RESULT: {each_response.strip()}\n"
        )

        previous_steps.append(each_step)

    return "===\n".join(previous_steps)


def extract_code_blocks(text: str, code_type: str | None = None) -> tuple[str, ...]:
    """
    Parses the code blocks from the text.

    Args:
    text: str: the text.

    Returns:
    list[str]: the code blocks.
    """

    if code_type is None:
        pattern = r'```(?:[a-zA-Z]+\n)?(.*?)```'
        return tuple(match.group(1).strip("`").strip() for match in re.finditer(pattern, text, re.DOTALL))

    return tuple(
        each_block.strip("`").strip()
        for each_block in re.findall(rf"```{code_type}(.*?)```", text, re.DOTALL | re.IGNORECASE))


def insert_docstring(func_code: str, docstring: str) -> str:
    # Parse the function code into an AST
    module = ast.parse(func_code)

    # Loop through the statements in the module to find the function
    for statement in module.body:
        # Check if the statement is a function definition
        if isinstance(statement, ast.FunctionDef):
            # Check for an existing docstring and remove it
            if (statement.body and isinstance(statement.body[0], ast.Expr)
                    and isinstance(statement.body[0].value, ast.Constant)
                    and isinstance(statement.body[0].value.value, str)):
                del statement.body[0]

            # Create a new docstring node
            docstring_node = ast.Constant(value=docstring, kind=None)

            # Insert the docstring node at the start of the function body
            statement.body.insert(0, ast.Expr(value=docstring_node))

            # Unparse the AST back into source code
            return ast.unparse(module)

    # If no function was found, return the original code
    return func_code


@dataclasses.dataclass
class Arg:
    name: str
    type: str
    description: str
    example_value: any


@dataclasses.dataclass
class Kwarg(Arg):
    default_value: any


@dataclasses.dataclass
class DocstringData:
    name: str
    summary: str
    description: str
    args: list[Arg]
    kwargs: list[Kwarg]
    return_type: str
    return_description: str


def compose_docstring(docstring_data: DocstringData) -> str:
    args_str = "\n".join(f"    {arg.name} ({arg.type}): {arg.description}\n" for arg in docstring_data.args)
    kwarg_lines = list()
    for each_kwarg in docstring_data.kwargs:
        if each_kwarg.default_value is None:
            kwarg_lines.append(
                f"    {each_kwarg.name} ({each_kwarg.type}, optional): {each_kwarg.description}"
            )
        else:
            kwarg_lines.append(
                f"    {each_kwarg.name} ({each_kwarg.type}): {each_kwarg.description.removesuffix('.')}. Defaults to {each_kwarg.default_value!r}."
            )
    args_str += "\n".join(kwarg_lines)

    example_args = ", ".join(
        [f"{each_arg.example_value!r}" for each_arg in docstring_data.args] +
        [f"{each_kwarg.name}={each_kwarg.example_value!r}" for each_kwarg in docstring_data.kwargs]
    )

    return (
        f"\"\"\"{docstring_data.summary}\n"
        f"\n"
        f"{docstring_data.description}\n"
        f"\n"
        f"Args:\n"
        f"{args_str}\n"
        f"\n"
        f"Example:\n"
        f"    >>> {docstring_data.name}({example_args})\n"
        f"\n"
        f"Returns:\n"
        f"    {docstring_data.return_type}: {docstring_data.return_description}\n"
        f"\"\"\""
    )
