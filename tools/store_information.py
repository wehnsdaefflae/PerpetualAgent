# coding=utf-8
import os


def store_information(information: str) -> str:
    """Stores information in a file.

    This function stores information in a file. It is useful to store large amounts of information for later retrieval. It serves as a memory.

    Example:
        >>> store_information("Four score and seven years ago our fathers brought forth, upon this continent, a new nation, conceived in liberty, and dedicated to the proposition that all men are created equal. [...]")
        "000041.txt"

    Args:
        information (str): A string representing the information to be stored.

    Returns:
        str: A string representing the name of the file where the information was stored.
    """
    largest_number = max([int(each_file_name.split(".")[0]) for each_file_name in os.listdir("memory") if each_file_name.endswith(".txt")])
    for i in range(largest_number):
        if not os.path.exists(f"memory/{i}.txt"):
            file_name = f"{i}.txt"
            break
    else:
        file_name = f"{largest_number + 1}.txt"

    with open("memory/" + file_name, mode="w") as file:
        file.write(information)

    return file_name
