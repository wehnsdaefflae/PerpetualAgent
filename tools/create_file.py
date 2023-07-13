def create_file(file_name: str, content: str) -> None:
    """Creates and populates a text file with the given content.

    This function dynamically generates a text file with a specified name and writes provided content into it. It's useful in situations where there's a need to generate text-based files dynamically, such as creating configuration files, generating reports, or storing data in simple formats like CSV or JSON.

    Example:
        >>> create_file("example.txt", "Sample text content")

    Args:
        file_name (str): The complete file path and name of the file to be created. It includes both the directory path and the filename.
        content (str): The string content that will be written into the file.

    Returns:
        None: This function doesn't return anything. It performs an action by creating and populating a file with the given content.
    """
    with open(file_name, 'w') as f:
        f.write(content)
