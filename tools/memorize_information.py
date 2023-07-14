# coding=utf-8
import os


def memorize_information(information: str) -> str:
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
