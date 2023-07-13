# coding=utf-8
import openai

from utils.llm_methods import LLMMethods


def summarize_text(text: str, len_summary: int, focus: str | None = None) -> str:
    """Generates a concise summary of the provided text based on the specified length and focus.

    This function aims to summarize any given text based on a user-specified character count and, if provided, a specific area of focus. It can be particularly useful in contexts such as academic research for generating paper abstracts, journalism for summarizing news articles, or data analysis where distilling lengthy reports into compact summaries is beneficial.

    Example:
        >>> summarize_text("Paris is the capital and most populous city of France.", 500, focus="population")

    Args:
        text (str): The original text to be summarized.
        len_summary (int): The desired character count for the summary. The summary's length will not exceed this value.
        focus (str, optional): A keyword or topic that should be emphasized in the summary. If no focus is provided, the summary will be generated based on the overall content.

    Returns:
        str: A succinct and focused summary of the input text, constructed to adhere to the user-specified length and focus constraints.
    """

    len_text = len(text)
    if len_summary >= len_text:
        return text

    focus_text = ""
    if focus is not None:
        focus_text = f" Focus on {focus}."

    instruction = f"Summarize the above text with {len_summary} characters.{focus_text}\n"

    if len_text > 5_000:
        text = LLMMethods.vector_summarize(instruction, text, model="gpt-3.5-turbo")
        return text

    prompt = (f"{text}\n"
              f"{instruction}")

    messages = [
        {"role": "user", "content": prompt}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    first_choice = response.choices[0]
    message = first_choice["message"]
    return message["content"]
