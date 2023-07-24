# index.py
from __future__ import annotations
from token_counter_b import FunctionDef, format_function_definitions


Message = dict[str, any]
Function = dict[str, any]


class Tiktoken:
    # Since there's no Tiktoken equivalent in Python, we create a dummy class to avoid errors.
    # Replace with actual functionality as needed.
    @staticmethod
    def encode(s: str) -> list[int]:
        return []

    @staticmethod
    def get_encoding(_type: str) -> Tiktoken:
        return Tiktoken()


encoder = None


def prompt_tokens_estimate(prompt: dict[str, list[Message] | list[Function]]) -> int:
    messages = prompt['messages']
    functions = prompt.get('functions')
    padded_system = False
    tokens = sum(message_tokens_estimate(m) for m in messages)

    tokens += 3

    if functions:
        tokens += functions_tokens_estimate(functions)

    if functions and any(m.get('role') == 'system' for m in messages):
        tokens -= 4

    return tokens


def string_tokens(s: str) -> int:
    global encoder
    if not encoder:
        encoder = Tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(s))


def message_tokens_estimate(message: Message) -> int:
    components = [comp for comp in [message.get('role'), message.get('content'), message.get('name')] if comp]
    tokens = sum(string_tokens(comp) for comp in components)

    if message.get('name'):
        tokens -= 1
    if message.get('function_call'):
        tokens += 3

    return tokens


def functions_tokens_estimate(funcs: list[FunctionDef]) -> int:
    prompt_definitions = format_function_definitions(funcs)
    tokens = string_tokens(prompt_definitions)
    tokens += 9
    return tokens
