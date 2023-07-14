def create_file(file_name: str, content: str) -> None:
    with open(file_name, 'w') as f:
        f.write(content)
