import logging
import sys


def logging_handlers() -> set[logging.StreamHandler]:
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setLevel(logging.INFO)
    handler_stdout.setFormatter(formatter)

    handler_file = logging.FileHandler("events.log")
    handler_file.setLevel(logging.DEBUG)
    handler_file.setFormatter(formatter)

    return {
        # handler_stdout,
        handler_file}
