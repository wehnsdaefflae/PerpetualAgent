# coding=utf-8
def calculate(what: str) -> str:
    """
    Performs arithmetic operations on a given string that represents a mathematical expression. The expression should conform to Python syntax and be constituted of numbers and arithmetic operators (+, -, *, /, **, etc.).

    Example:
        >>> calculate("2 + 3 * 4")

    Args:
        what (str): A string representation of a mathematical expression in Python syntax.

    Returns:
        str: The result of the evaluated expression as a string. If the evaluation fails (due to incorrect syntax or undefined operations), an error message will be returned.
    """
    try:
        return eval(what)

    except Exception as e:
        return f"{e}"
