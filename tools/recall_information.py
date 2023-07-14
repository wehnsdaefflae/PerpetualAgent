# coding=utf-8


def recall_information(file_name: str) -> str:
    with open("memory/" + file_name, mode="r") as file:
        return file.read()
