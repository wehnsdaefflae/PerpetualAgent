# coding=utf-8

def calculate(what: str) -> str:
    try:
        return eval(what)

    except Exception as e:
        return f"{e}"
