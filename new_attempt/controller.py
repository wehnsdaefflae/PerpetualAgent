from typing import Callable

from new_attempt.model import Model
from new_attempt.view import View


class Controller:
    def __init__(self, model: Model, view: View) -> None:
        self.model = model
        self.view = view
        self.triggers = dict()

    def register(self, key: str, on_change: Callable[..., any]) -> None:
        self.triggers[key] = on_change

    def send(self, key: str, *args: any, **kwargs: any) -> any:
        action = self.triggers.get(key)
        if action is None:
            return None

        value = action(*args, **kwargs)
        return value

