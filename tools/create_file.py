def create_file(file_name: str, content: str) -> None:
    """
    Create a file with the given name and content.

    Example:
        >>> create_file("hello.txt", "Hello World")

    Args:
        file_name (str): the path and name of the file to create.
        content (str): the content to write to the file.

    Returns:
        None
    """
    with open(file_name, 'w') as f:
        f.write(content)
