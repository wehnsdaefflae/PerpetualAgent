# coding=utf-8
from __future__ import annotations


class A:
    def __init__(self) -> None:
        print("init")

    def __enter__(self) -> A:
        print("enter")
        return self

    def __exit__(self, exc_type: any, exc_value: any, traceback: any) -> None:
        print("exit")


def main() -> None:
    with A() as a:
        print("first with")

    with a:
        print("second with")


if __name__ == "__main__":
    main()
