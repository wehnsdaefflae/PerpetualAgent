# coding=utf-8
def calculate(what: str) -> str:
    """
    Calculate a mathematical expression in Python syntax.

    Example:
        >>> calculate("4 * 7 / 3")

    Args:
        what (str): the expression to calculate.

    Returns:
        str: the result of the calculation.
    """
    try:
        return eval(what)

    except Exception as e:
        return f"{e}"
