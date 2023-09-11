# coding=utf-8
from dataclasses import dataclass
import openai
from pdfminer.high_level import extract_text

from utils.misc import segment_text


def indent(text: str, indent_str: str = "    ") -> str:
    return "\n".join(f"{indent_str}{line}" for line in text.splitlines())


@dataclass(frozen=True)
class Response:
    output: str
    summary: str

    def __str__(self) -> str:
        return f"Response(output='{self.output}', summary='{self.summary}')"


def summarize(
        content: str, *args: any,
        context: str = "[not provided]",
        additional_instruction: str | None = None,
        min_length: int = 300,
        _content_tag: str = "Content",
        _context_tag: str = "Context",
        **kwargs: any) -> str:

    # todo: problem: might return just very little remaining tokens
    while True:
        summarize_prompt = (
            f"<{_context_tag}>\n"
            f"{indent(context).rstrip()}\n"
            f"</{_context_tag}>\n"
            f"\n"
            f"<{_content_tag}>\n"
            f"{indent(content).rstrip()}\n"
            f"</{_content_tag}>\n"
            f"\n"
            f"Any information provided in the outermost `{_context_tag}` tag is known. "
            f"Take this into account when summarizing the text in the outermost `{_content_tag}` tag."
        )

        if additional_instruction is not None:
            summarize_prompt += f" {additional_instruction.strip()}"

        messages = [{"role": "user", "content": summarize_prompt}]
        try:
            response_message = openai.ChatCompletion.create(*args, messages=messages, **kwargs)
            first_choice, = response_message.choices
            first_message = first_choice.message
            output = first_message.content
            if len(output) >= min_length or len(content) < min_length:
                return output

        except openai.error.OpenAIError as e:
            if e.code != "context_length_exceeded":
                raise e

            print("too much, segmenting")
            rolling_summary = None
            summaries = list()
            segments = segment_text(content, segment_length=2_000)
            for i, each_segment in enumerate(segments):
                print(f"segment {i + 1} of approx {len(content) // len(each_segment) + 1} segments")
                if rolling_summary is None:
                    each_summary = summarize(each_segment, *args, **kwargs)
                    rolling_summary = each_summary

                else:
                    each_summary = summarize(each_segment, *args, context=rolling_summary, **kwargs)
                    rolling_summary = summarize(f"{rolling_summary}\n{each_summary}", *args, **kwargs)

                summaries.append(each_summary)

            content = "\n".join(summaries)
            print("restarting with summarized content...")


def respond(
        instruction: str, *args: any,
        data: str | None = None,
        recap: str | None = None,
        max_recap_length: int = 1_000,
        max_instruction_len: int = 1_000,
        min_data_len: int = 10,
        _recap_tag: str = "ConversationLog",
        _data_tag: str = "AdditionalData",
        **kwargs: any) -> Response:

    len_instruction = len(instruction)
    if len_instruction >= max_instruction_len:
        raise ValueError(f"Instruction too long: {len_instruction} >= {max_instruction_len}")

    if data is None:
        data_element = ""

    else:
        data_element = (
            f"<{_data_tag}>\n"
            f"{indent(data).rstrip()}\n"
            f"</{_data_tag}>\n"
            f"\n"
        )

    if recap is None:
        recap_element = ""

    else:
        recap_element = (
            f"<{_recap_tag}>\n"
            f"{indent(recap).rstrip()}\n"
            f"</{_recap_tag}>\n"
            f"\n"
        )

    while True:
        prompt = (
            f"{recap_element}"
            f"{data_element}"
            f"{instruction.rstrip()}"
        )

        messages = [{"role": "user", "content": prompt}]
        try:
            response_message = openai.ChatCompletion.create(*args, messages=messages, **kwargs)
            first_choice, = response_message.choices
            first_message = first_choice.message
            output = first_message.content

            updated_recap = (
                                (f"" if recap is None else f"{recap}\n") +
                                f"<UserRequest>\n"
                                f"{indent(instruction).rstrip()}\n"
                                f"</UserRequest>\n"
                                f"\n" +
                                f"<AssistantResponse>\n"
                                f"{indent(output).rstrip()}\n"
                                f"</AssistantResponse>"
            )

            if len(updated_recap) >= max_recap_length:
                summary = summarize(
                    updated_recap,
                    *args,
                    additional_instruction="Be very concise but preserve all literal information as well as the conversational character.",
                    **kwargs)
                updated_recap = (
                    f"<ConversationSummary>\n"
                    f"{indent(summary).rstrip()}\n"
                    f"</ConversationSummary>"
                )

            return Response(output, updated_recap)

        except openai.error.OpenAIError as e:
            if e.code != "context_length_exceeded":
                raise e

            if len(data) < min_data_len:
                raise ValueError("Data payload small, but request still too long.") from e

            data = summarize(data, *args, context=recap, **kwargs)


def run_dialog() -> None:
    summary = None
    while True:
        instructions = input("User: ")
        response = respond(instructions, model="gpt-3.5-turbo", recap=summary)
        output = response.output
        print(f"Assistant: {output}")
        summary = response.summary
        print()
        print(f"Summary:\n{summary}")
        print()
        print()


def run_summarize() -> None:
    text = extract_text("/home/mark/Downloads/2308.10379.pdf")
    summary = summarize(text, model="gpt-3.5-turbo")
    print(summary)


def main() -> None:
    openai.api_key_path = "resources/openai_api_key.txt"

    run_dialog()
    # run_summarize()


if __name__ == "__main__":
    main()
