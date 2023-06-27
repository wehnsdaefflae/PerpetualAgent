# coding=utf-8
import openai


def summarize_text(text: str, len_summary: int, focus: str | None = None) -> str:
    """
    Generates a summary of a provided text of a specified length and, optionally, with a specified focus. Can be applied in any context where summarizing large amounts of text is needed, such as abstract generation for academic papers, summarizing news articles, or creating concise reports from lengthy data.

    Example:
        >>> summarize_text("Paris is the capital and most populous city of France.", 500, focus="population")

    Args:
        text (str): The text to be summarized.
        len_summary (int): The desired character count of the summary.
        focus (str, optional): An optional focus for the summary.

    Returns:
        str: A summary of the input text with the specified length and focus.
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
