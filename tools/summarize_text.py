# coding=utf-8
from utils.basic_llm_calls import openai_chat
from utils.llm_methods import LLMMethods


def summarize_text(text: str, len_summary: int, focus: str | None = None) -> str:
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

    response = openai_chat(
        "summarize",
        ack=False,
        model="gpt-3.5-turbo",
        messages=messages
    )

    first_choice = response.choices[0]
    message = first_choice["message"]
    return message["content"]
