# coding=utf-8
import openai


def finalize(request: str, intermediate_results: list[str]) -> str:
    """
    Generates a final response for a request by integrating the intermediate results. Applicable in cases where there's a need for parsing a sequence of intermediate responses derived from the initial request, synthesizing them into a meaningful final response.

    Example:
        >>> finalize("What is the result of 4 * 7 / 3?", ["Four times seven is 28", "28 divided by three equals approximately 9.3"])

    Args:
        request (str): The original request made by the user.
        intermediate_results (list[str]): The list of intermediate results that are relevant to fulfilling the request.

    Returns:
        str: The final synthesized response, derived from the intermediate results in relation to the original request.
    """
    intermediate_str = "\n\n".join(intermediate_results)
    prompt = (f"Use the intermediate results to compose a final response to the initial request.\n"
              f"\n"
              f"Intermediate results:\n"
              f"{intermediate_str}\n"
              f"===\n"
              f"Initial request:\n"
              f"{request}")

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
