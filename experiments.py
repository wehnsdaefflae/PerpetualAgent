# coding=utf-8
from dataclasses import dataclass
import openai
from utils.misc import segment_text


def indent(text: str, indent_str: str = "    ") -> str:
    return "\n".join(f"{indent_str}{line}" for line in text.splitlines())


@dataclass(frozen=True)
class Response:
    output: str
    summary: str


def summarize(
        content: str, *args: any,
        context: str = "[no context provided]",
        content_tag: str = "Content",
        context_tag: str = "Context",
        **kwargs: any) -> str:

    while True:
        summarize_prompt = (
            f"<{context_tag}>\n"
            f"{indent(context)}\n"
            f"</{context_tag}>\n"
            f"\n"
            f"<{content_tag}>\n"
            f"{indent(content)}\n"
            f"</{content_tag}>\n"
            f"\n"
            f"The information in the outermost `{context_tag}` tag is known. "
            f"Summarize only unique details from the text in the outermost `{content_tag}` tag."
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

            rolling_summary = None
            summaries = list()
            segments = segment_text(content)
            for i, each_segment in enumerate(segments):
                each_summary = summarize(each_segment, *args, context=rolling_summary, **kwargs)
                summaries.append(each_summary)
                if i < 1:
                    rolling_summary = each_summary
                else:
                    rolling_summary = summarize(f"{rolling_summary}\n{each_summary}", *args, **kwargs)

            content = "\n".join(summaries)


def respond(
        instruction: str, data: str, *args: any,
        recap: str = "[conversation did not start yet]",
        max_instruction_len: int = 1_000,
        min_data_len: int = 10,
        recap_tag: str = "Recap",
        data_tag: str = "Data",
        **kwargs: any) -> Response:

    len_instruction = len(instruction)
    if len_instruction >= max_instruction_len:
        raise ValueError(f"Instruction too long: {len_instruction} >= {max_instruction_len}")

    while True:
        prompt = (
            f"<{recap_tag}>\n"
            f"{indent(recap)}\n"
            f"</{recap_tag}>\n"
            f"\n"
            f"<{data_tag}>\n"
            f"{indent(data)}\n"
            f"</{data_tag}>\n"
            f"\n"
            f"{instruction}"
        )

        messages = [{"role": "user", "content": prompt}]
        try:
            response_message = openai.ChatCompletion.create(*args, messages=messages, **kwargs)
            first_message = response_message.choices[0]
            output = first_message.content

            updated_recap = summarize(
                f"RECAP: {recap}\n" +
                f"USER: {instruction}\n" +
                f"ASSISTANT: {output}",
                *args, **kwargs)

            return Response(output, updated_recap)

        except openai.error.OpenAIError as e:
            if e.code != "context_length_exceeded":
                raise e

            if len(data) < min_data_len:
                raise ValueError("Data payload small, but request still too long.") from e

            data = summarize(data, *args, context=recap, **kwargs)


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
