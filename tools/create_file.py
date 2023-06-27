def create_file(file_name: str, content: str) -> None:
    """
    Generates a text file with a specified name and populates it with provided content.

    Useful for cases requiring the dynamic creation of text-based files, such as for configuration files,
    report generation, or data storage in simple formats like CSV or JSON.

    Example:
        >>> create_file("example.txt", "Sample text content")

    Args:
        file_name (str): Specifies the path and name for the file to be created.
        content (str): String to be written into the file as its contents.

    Returns:
        None
    """
    with open(file_name, 'w') as f:
        f.write(content)
