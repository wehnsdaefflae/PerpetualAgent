# coding=utf-8
import ast
import datetime
import re
import logging

from typing import Generator

from utils.logging_handler import logging_handlers

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

handlers = logging_handlers()
for each_handler in handlers:
    LOGGER.addHandler(each_handler)


def truncate(string: str, limit: int, indicator: str = "[...]", at_start: bool = False) -> str:
    if limit >= len(string):
        return string

    if at_start:
        return indicator + string[len(string) - limit:]

    return string[:limit - len(indicator)] + indicator


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
    indented_docstring = "\n".join(("" if i < 1 else "    ") + each_line for i, each_line in enumerate(docstring.splitlines())) + "\n    "

    # Loop through the statements in the module to find the first function
    for statement in module.body:
        # Check if the statement is a function definition
        if isinstance(statement, ast.FunctionDef):
            # Check for an existing docstring and remove it
            # Here, it is important to note that the first string literal in the function is removed
            # regardless of whether it is used as a docstring or not.
            if (statement.body and isinstance(statement.body[0], ast.Expr)
                    and isinstance(statement.body[0].value, ast.Constant)
                    and isinstance(statement.body[0].value.value, str)):
                del statement.body[0]

            # Create a new docstring node
            # From Python 3.8 and onwards, all constant values are represented by ast.Constant nodes,
            # ast.Str is deprecated.
            docstring_node = ast.Constant(value=indented_docstring, kind=None)

            # Insert the docstring node at the start of the function body
            statement.body.insert(0, ast.Expr(value=docstring_node))

            # Unparse the AST back into source code
            # The unparse method is part of the astunparse package, which needs to be installed separately.
            return ast.unparse(module)

    # If no function was found, raise an error
    raise SyntaxError("No function definition found")


def compose_docstring(docstring_data: dict[str, any]) -> str:
    args_positional = [each_arg for each_arg in docstring_data["args"] if not each_arg["is_keyword_argument"]]
    args_keyword = [each_arg for each_arg in docstring_data["args"] if each_arg["is_keyword_argument"]]
    # todo: example arguments and return_value and up as string insearch of actual type
    arg_lines = list()
    for each_arg in args_positional:
        one_line_description = " ".join(each_arg["description"].splitlines())
        each_line = f"{each_arg['name'].strip()} ({each_arg['python_type'].strip()}): {one_line_description}"
        arg_lines.append("    " + each_line.strip())

    for each_kwarg in args_keyword:
        each_line = f"{each_kwarg['name'].strip()} "
        one_line_description = " ".join(each_kwarg['description'].splitlines())
        if ". Default" not in one_line_description:
            one_line_description = f"{one_line_description.removesuffix('.')}. Defaults to {each_kwarg['default_value']!r}."

        if each_kwarg["default_value"] is None:
            each_line += f"(Optional[{each_kwarg['python_type'].strip()}]): {one_line_description}"
        else:
            each_line += f"({each_kwarg['python_type'].strip()}): {one_line_description}"

        arg_lines.append("    " + each_line.strip())

    if len(arg_lines) < 1:
        args_str = "    None"
    else:
        args_str = "\n".join(arg_lines)

    example_args = ", ".join(
        [f"\"{each_arg['example_value']}\"" if each_arg["python_type"] == "str" else f"{each_arg['example_value']}" for each_arg in args_positional] +
        [f"{each_kwarg['name']}=\"{each_kwarg['example_value']}\"" if each_kwarg["python_type"] == "str" else f"{each_kwarg['name']}={each_kwarg['example_value']}"
         for each_kwarg in args_keyword]
    )

    return_value = docstring_data["return_value"]
    if return_value["python_type"] == "None":
        example_return_str = ""
        return_str = "None"
    else:
        if return_value["python_type"] == "str":
            example_return_str = f"    '{return_value['example_value']}'\n"
        else:
            example_return_str = f"    {return_value['example_value']}\n"
        one_line_description = ' '.join(return_value['description'].splitlines())
        return_str = f"{return_value['python_type']}: {one_line_description}"

    return (
        f"{' '.join(docstring_data['summary'].splitlines())}\n"
        f"\n"
        f"{' '.join(docstring_data['description'].splitlines())}\n"
        f"\n"
        f"Args:\n"
        f"{args_str}\n"
        f"\n"
        f"Example:\n"
        f"    >>> {docstring_data['name']}({example_args})\n"
        f"{example_return_str}"
        f"\n"
        f"Returns:\n"
        f"    {return_str}\n"
    )


def segment_text(text: str, segment_length: int = 500, overlap: int = 100, truncation_sign: str = "[...]") -> Generator[str, None, None]:
    len_t = len(text)
    if segment_length >= len_t:
        yield text
        return

    len_s = len(truncation_sign)
    cursor = 0
    while cursor < len_t:
        if cursor < 1:
            cursor_end = cursor + segment_length - len_s
            new_cursor = cursor_end - overlap
            if cursor >= new_cursor:
                raise ValueError("Segment length is too short.")
            segment = f"{text[cursor:cursor_end]}{truncation_sign}"
            cursor = new_cursor
            yield segment

        elif cursor + segment_length < len_t:
            cursor_end = cursor + segment_length - 2 * len_s
            new_cursor = cursor_end - overlap
            if cursor >= new_cursor:
                raise ValueError("Segment length is too short.")
            segment = f"{truncation_sign}{text[cursor:cursor_end]}{truncation_sign}"
            cursor = new_cursor
            yield segment

        else:
            segment = f"{truncation_sign}{text[cursor:]}"
            yield segment
            return


def get_date_name() -> str:
    now = datetime.datetime.now()
    folder_name = now.strftime("%Y_%m_%d_%H_%M_%S")
    return folder_name
