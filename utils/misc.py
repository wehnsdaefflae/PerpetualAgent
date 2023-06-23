import re


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
