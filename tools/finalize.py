# coding=utf-8
import openai


def finalize(request: str, intermediate_results: list[str]) -> str:
    """
    Finalizes a request by summarizing intermediate results into a final response.

    Example:
        >>> finalize("What is the result of 4 * 7 / 3?", ["Four times seven is 28", "28 divided by three equals approximately 9.3"])

    Args:
        request (str): the original request.
        intermediate_results (list[str]): the intermediate results.

    Returns:
        str: the final response.
    """
    intermediate_str = "\n\n".join(intermediate_results)
    prompt = (f"Intermediate results:\n"
              f"{intermediate_str}\n"
              f"===\n"
              f"Initial request:\n"
              f"{request}\n"
              f"===\n"
              f"Use information from the intermediate results to compose a final response to the initial request.")

    messages = [
        {"role": "user", "content": prompt}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=messages
    )

    first_choice = response.choices[0]
    message = first_choice["message"]
    return message["content"]
