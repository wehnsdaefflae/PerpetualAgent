# coding=utf-8
import openai


def summarize_text(text: str, len_summary: int, focus: str | None = None) -> str:
    """
    Summarize the text with an approximate number of total characters.

    Example:
        >>> summarize_text("Paris is the capital and most populous city of France.", 500, focus="population")

    Args:
        text (str): the information.
        len_summary (int): the length of the summary.
        focus (str): the focus of the summary.

    Returns:
        str: a summary of the information.
    """
    if len(text) <= len_summary:
        return text

    focus_text = ""
    if focus is not None:
        focus_text = f" Focus on {focus}."

    prompt = f"{text}\n\nSummarize the above text with {len_summary} characters.{focus_text}\n\nSummary:"

    messages = [
        {"role": "user", "content": prompt}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages
    )

    first_choice = response.choices[0]
    message = first_choice["message"]
    return message["content"]
