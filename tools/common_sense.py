# coding=utf-8
import openai


def common_sense(request: str) -> str:
    """
    Use common sense to respond to a request.

    Example:
        >>> common_sense("What is the capital of France.")

    Args:
        request (str): the request.

    Returns:
        str: a response to the request.
    """

    messages = [
        {"role": "user", "content": request}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages
    )

    first_choice = response.choices[0]
    message = first_choice["message"]
    return message["content"]
