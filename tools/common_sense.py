# coding=utf-8
import openai


def common_sense(request: str) -> str:
    if len(request) > 500:
        raise ValueError("The request must be less than 500 characters long.")

    messages = [
        {"role": "user", "content": request}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    first_choice = response.choices[0]
    message = first_choice["message"]
    return message["content"]
