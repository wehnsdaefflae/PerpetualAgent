# coding=utf-8
import os


def retrieve_information(file_name: str) -> str:
    """Retrieves information from a file.

    This function retrieves information in a file. It is useful to recall large amounts of information that have been saved previously. It serves as a memory.

    Example:
        >>> retrieve_information("000041.txt")
        "Four score and seven years ago our fathers brought forth, upon this continent, a new nation, conceived in liberty, and dedicated to the proposition that all men are created equal. [...]"

    Args:
        file_name (str): A string representing the name of the file where the information was stored.

    Returns:
        str: A string representing the information that was stored in the file.
    """
    with open("memory/" + file_name, mode="r") as file:
        return file.read()
