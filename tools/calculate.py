# coding=utf-8
def calculate(what: str) -> str:
    """Evaluates and performs arithmetic operations on a given mathematical expression string, following Python syntax.

    This function takes a string representation of a mathematical expression that follows Python syntax. It handles numbers and various arithmetic operators such as addition (+), subtraction (-), multiplication (*), division (/), and exponentiation (**). It evaluates the expression and returns the result as a string. In case of evaluation failure due to incorrect syntax or undefined operations, it returns an error message.

    Example:
        >>> calculate("2 + 3 * 4")

    Args:
        what (str): A string representing a mathematical expression conforming to Python syntax.

    Returns:
        str: The result of the evaluated expression. If the evaluation is unsuccessful, an error message will be returned.
    """
    try:
        return eval(what)

    except Exception as e:
        return f"{e}"
