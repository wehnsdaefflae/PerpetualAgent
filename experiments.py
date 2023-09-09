# coding=utf-8
from dataclasses import dataclass

import openai

from utils.misc import segment_text


@dataclass(frozen=True)
class Response:
    output: str
    summary: str


def indent(text: str, indent_str: str = "    ") -> str:
    return "\n".join(f"{indent_str}{line}" for line in text.splitlines())


def summarize(text: str, *args: any, context: str | None = None, **kwargs: any) -> str:
    while True:
        if context is None:
            context_prompt = ""
            instruction = "Summarize the above text in the outermost `Content` tag.\n"

        else:
            context_prompt = (
                f"<DontRepeat>\n"
                f"{indent(context)}\n"
                f"</DontRepeat>\n"
                f"\n"
            )
            instruction = (
                "Summarize the above text in the outermost `Content` tag. In your summary, consider the information in the outermost `DontRepeat` tag as already known to the reader."
            )

        summarize_prompt = (
            f"{context_prompt}"
            f"<Content>\n"
            f"{indent(text)}\n"
            f"</Content>\n"
            f"\n"
            f"{instruction}"
        )

        message = {"role": "user", "content": summarize_prompt}
        try:
            response_message = openai.ChatCompletion.create(*args, messages=[message], **kwargs)
            first_message = response_message.choices[0]
            output = first_message.content
            return output

        except openai.error.OpenAIError as e:
            if e.code != "context_length_exceeded":
                raise e

            sub_context = None
            summaries = list()
            for i, each_segment in enumerate(segment_text(text)):
                each_summary = summarize(each_segment, *args, context=sub_context, **kwargs)
                summaries.append(each_summary)
                if i < 1:
                    sub_context = each_summary
                else:
                    sub_context = summarize(f"{sub_context}\n{each_summary}", *args, **kwargs)

            text = "\n".join(summaries)


def prompt(instruction: str, payload: str, *args: any, summary: str | None = None, **kwargs: any) -> Response:
    len_instruction = len(instruction)
    if len_instruction >= 1_000:
        raise ValueError("Instruction too long")

    while True:
        prompt_text = (
            f"<Progress>\n"
            f"{indent(summary)}\n"
            f"</Progress>\n"
            f"\n"
            f"<Important>\n"
            f"{indent(payload)}\n"
            f"</Important>\n"
            f"\n"
            f"{instruction}"
        )

        message = {"role": "user", "content": prompt_text}
        try:
            response_message = openai.ChatCompletion.create(*args, messages=[message], **kwargs)
            first_message = response_message.choices[0]
            output = first_message.content

            new_summary = summarize(
                f"<ConversationLog>\n"
                f"{indent(summary)}\n"
                f"</ConversationLog>\n"
                f"\n"
                f"<UserRequest>\n"
                f"{indent(instruction)}\n"
                f"</UserRequest>\n"
                f"\n"
                f"<AssistantResponse>\n"
                f"{indent(output)}\n"
                f"</AssistantResponse>\n"
                f"\n",
                *args, **kwargs)

            return Response(output, new_summary)

        except openai.error.OpenAIError as e:
            if e.code != "context_length_exceeded":
                raise e

            if len(payload) < 1_000:
                raise ValueError("Payload small, but request still too long.") from e

            payload = summarize(payload, *args, context=summary, **kwargs)


def main() -> None:
    openai.api_key_path = "resources/openai_api_key.txt"
    messages = [
        {
            "role": "user",
            "content": "Hello, I am a human." * 1_000
        },
    ]
    try:
        response_message = openai.ChatCompletion.create(messages=messages, model="gpt-3.5-turbo")
    except openai.error.OpenAIError as e:
        print(e)


if __name__ == "__main__":
    main()
