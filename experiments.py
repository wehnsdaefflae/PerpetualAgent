# coding=utf-8
from dataclasses import dataclass
import openai
from pdfminer.high_level import extract_text

from utils.misc import segment_text


def indent(text: str, indent_str: str = "    ", times: int = 1) -> str:
    return "\n".join(f"{indent_str * times}{line}" for line in text.splitlines())


@dataclass(frozen=True)
class Response:
    output: str
    summary: str

    def __str__(self) -> str:
        return f"Response(output='{self.output}', summary='{self.summary}')"


def summarize(
        content: str, *args: any,
        context: str | None = None,
        additional_instruction: str | None = None,
        min_length: int = 300,
        _content_tag: str = "Content",
        _context_tag: str = "Context",
        **kwargs: any) -> str:
    # todo: problem: might return just very little remaining tokens
    while True:
        if context is None:
            context_element = ""
            instruction = f"Summarize the text in the outermost `{_content_tag}` tag."

        else:
            context_element = (
                f"<{_context_tag}>\n"
                f"{indent(context).rstrip()}\n"
                f"</{_context_tag}>\n"
                f"\n"
            )
            instruction = (
                f"Any information provided in the outermost `{_context_tag}` tag is known. "
                f"Take this into account when summarizing the text in the outermost `{_content_tag}` tag."
            )

        if additional_instruction is not None:
            instruction += f" {additional_instruction.strip()}"

        summarize_prompt = (
            f"{context_element}"
            f"<{_content_tag}>\n"
            f"{indent(content).rstrip()}\n"
            f"</{_content_tag}>\n"
            f"\n"
            f"{instruction}"
        )

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
        _recap_tag: str = "ConversationLog",
        _summary_tag: str = "ConversationSummary",
        _data_tag: str = "AdditionalData",
        **kwargs: any) -> Response:

    while True:
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

        prompt = (
                recap_element +
                data_element +
                instruction.rstrip()
        )

        messages = [{"role": "user", "content": prompt}]
        try:
            response_message = openai.ChatCompletion.create(*args, messages=messages, **kwargs)
            first_choice, = response_message.choices
            first_message = first_choice.message
            output = first_message.content

            updated_recap_content = (
                    (f"" if recap is None else f"{recap}\n") +
                    "<UserRequest>\n" +
                    f"{indent(instruction).rstrip()}\n" +
                    f"</UserRequest>\n" +
                    f"\n" +
                    f"<AssistantResponse>\n" +
                    f"{indent(output).rstrip()}\n" +
                    f"</AssistantResponse>"
            )

            return Response(output, updated_recap_content)

        except openai.error.OpenAIError as e:
            if e.code != "context_length_exceeded":
                raise e

            len_instruction = len(instruction)
            len_recap = -1 if recap is None else len(recap)
            len_data = -1 if data is None else len(data)

            if len_instruction >= len_data and len_instruction >= len_recap:
                instruction = summarize(instruction, *args, context=recap, **kwargs)

            elif len_recap >= len_instruction and len_recap >= len_data:
                focus_conversation = "Be very concise but preserve literal information and conversational character."
                recap_text = summarize(recap, *args, additional_instruction=focus_conversation, **kwargs)
                recap = (
                    f"<{_summary_tag}>\n" +
                    f"{indent(recap_text.rstrip())}\n" +
                    f"</{_summary_tag}>"
                )

            elif len_data >= len_instruction and len_data >= len_recap:
                focus_instruction = f"Focus on information relevant to the following request: \"{instruction.strip()}\""
                data = summarize(data, *args, context=recap, additional_instructions=focus_instruction, **kwargs)

            else:
                raise ValueError(
                    f"Undefined component lengths: "
                    f"len_instruction {len_instruction}, len_recap {len_recap}, len_data {len_data}."
                ) from e


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
