from typing import Callable


TRIGGERS = dict()


def register(key: str, on_change: Callable[..., any]) -> None:
    TRIGGERS[key] = on_change


def send(key: str, *args: any, **kwargs: any) -> any:
    action = TRIGGERS.get(key)
    if action is None:
        return None

    value = action(*args, **kwargs)
    return value
