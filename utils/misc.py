# coding=utf-8
import ast
import re


def truncate(string: str, limit: int, indicator: str = "[...]", at_start: bool = False) -> str:
    if limit >= len(string):
        return string

    if at_start:
        return indicator + string[len(string) - limit:]

    return string[:limit - len(indicator)] + indicator


def extract_docstrings(text: str) -> tuple[str, ...]:
    """
    This function extracts all the triple quoted strings from the given text.

    Parameters:
    text (str): The input string from which triple quoted strings need to be extracted.

    Returns:
    List[str]: A list of all triple quoted strings including the triple quotes.
    """

    # The pattern for triple quoted strings.
    pattern = r'\'\'\'(.*?)\'\'\'|\"\"\"(.*?)\"\"\"'

    # Find all the matches for the pattern and flatten the result.
    matches = re.findall(pattern, text, re.DOTALL)
    flattened_matches = [quote for match in matches for quote in match if quote]

    # Prepend and append the quotes back to the results.
    return tuple(f'"""\n{match.strip()}\n"""' if text.find(f'"""{match}"""') >= 0 else f"'''\n{match.strip()}\n'''" for match in flattened_matches)


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
