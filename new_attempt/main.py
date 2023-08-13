from new_attempt.controller import Controller
from new_attempt.model import Model
from new_attempt.view import View


def main():
    # https://chat.openai.com/share/4dcf41b8-436c-48d7-b909-fa3c7b6d82f4

    view = View()
    model = Model()
    controller = Controller(model, view)


if __name__ in {"__main__", "__mp_main__"}:
    main()
