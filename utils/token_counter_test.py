from typing import TypedDict

import openai
import pytest

from utils.token_counter_a import prompt_tokens_estimate


class Function(TypedDict):
    name: str
    description: str | None
    parameters: dict


class Message(TypedDict):
    role: str
    content: str
    function_call: dict | None


class Example(TypedDict):
    messages: list[Message]
    functions: list[Function] | None
    tokens: int
    validate: bool | None


r = {
    "model": "gpt-3.5-turbo",
    "temperature": 0,
    "functions": [
        {
            "name": "do_stuff",
            "parameters": {}
        }
    ],
    "messages": [
        {
            "role": "system",
            "content": "hello:"
        },
    ]
}
TEST_CASES = [
    {
        "messages": [{"role": "user", "content": "hello"}],
        "tokens": 8
    },
    {
        "messages": [{"role": "user", "content": "hello world"}],
        "tokens": 9
    },
    {
        "messages": [{"role": "system", "content": "hello"}],
        "tokens": 8
    },
    {
        "messages": [{"role": "system", "content": "hello:"}],
        "tokens": 9
    },
    {
        "messages": [
            {"role": "system", "content": "# Important: you're the best robot"},
            {"role": "user", "content": "hello robot"},
            {"role": "assistant", "content": "hello world"},
        ],
        "tokens": 27
    },
    {
        "messages": [{"role": "user", "content": "hello"}],
        "functions": [
            {
                "name": "foo",
                "parameters": {"type": "object", "properties": {}}
            }
        ],
        "tokens": 31
    },
    {
        "messages": [{"role": "user", "content": "hello"}],
        "functions": [
            {
                "name": "foo",
                "description": "Do a foo",
                "parameters": {"type": "object", "properties": {}}
            }
        ],
        "tokens": 36
    },
    {
        "messages": [{"role": "user", "content": "hello"}],
        "functions": [
            {
                "name": "bing_bong",
                "description": "Do a bing bong",
                "parameters": {
                    "type": "object",
                    "properties": {"foo": {"type": "string"}},
                }
            }
        ],
        "tokens": 49
    },
    {
        "messages": [{"role": "user", "content": "hello"}],
        "functions": [
            {
                "name": "bing_bong",
                "description": "Do a bing bong",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "foo": {"type": "string"},
                        "bar": {"type": "number", "description": "A number"},
                    }
                }
            }
        ],
        "tokens": 57
    },
    {
        "messages": [{"role": "user", "content": "hello"}],
        "functions": [
            {
                "name": "bing_bong",
                "description": "Do a bing bong",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "foo": {
                            "type": "object",
                            "properties": {
                                "bar": {"type": "string", "enum": ["a", "b", "c"]},
                                "baz": {"type": "boolean"}
                            }
                        },
                    }
                }
            }
        ],
        "tokens": 68
    },
    {
        "messages": [
            {"role": "user", "content": "hello world"},
            {"role": "function", "name": "do_stuff", "content": "{}"},
        ],
        "tokens": 15
    },
    {
        "messages": [
            {"role": "user", "content": "hello world"},
            {"role": "function", "name": "do_stuff", "content": '{"foo": "bar", "baz": 1.5}'},
        ],
        "tokens": 28
    },
    {
        "messages": [
            {"role": "function", "name": "dance_the_tango", "content": '{"a": { "b" : { "c": false}}}'},
        ],
        "tokens": 24
    },
    {
        "messages": [
            {"role": "assistant", "content": "", "function_call": {"name": "do_stuff", "arguments": '{"foo": "bar", "baz": 1.5}'}},
        ],
        "tokens": 26
    },
    {
        "messages": [
            {"role": "assistant", "content": "", "function_call": {"name": "do_stuff", "arguments": '{"foo":"bar", "baz":\n\n 1.5}'}},
        ],
        "tokens": 25
    },
    {
        "messages": [
            {"role": "system", "content": "Hello"},
            {"role": "user", "content": "Hi there"},
        ],
        "functions": [
            {
                "name": "do_stuff",
                "parameters": {"type": "object", "properties": {}}
            }
        ],
        "tokens": 35
    },
    {
        "messages": [
            {"role": "system", "content": "Hello:"},
            {"role": "user", "content": "Hi there"},
        ],
        "functions": [
            {
                "name": "do_stuff",
                "parameters": {"type": "object", "properties": {}}
            }
        ],
        "tokens": 35
    },
    {
        "messages": [
            {"role": "system", "content": "Hello:"},
            {"role": "system", "content": "Hello"},
            {"role": "user", "content": "Hi there"},
        ],
        "functions": [
            {
                "name": "do_stuff",
                "parameters": {"type": "object", "properties": {}}
            }
        ],
        "tokens": 40
    },
]

validate_all = False
openai_timeout = 10000


@pytest.mark.parametrize("example", TEST_CASES)
def test_token_counts(example: Example):
    openai.api_key_path = "../resources/openai_api_key.txt"

    # test data matches openai
    if validate_all or example.get("validate", False):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=example["messages"],
            functions=example.get("functions", []),
            max_tokens=10,
        )
        assert response["usage"]["prompt_tokens"] == example["tokens"]

    # estimate is correct
    assert prompt_tokens_estimate({"messages": example["messages"], "functions": example.get("functions")}) == example["tokens"]
