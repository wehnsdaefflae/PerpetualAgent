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
        min_length: int = 300,
        _content_tag: str = "Content",
        _context_tag: str = "Context",
        **kwargs: any) -> str:

    # todo: problem: might return just very little remaining tokens
    while True:
        summarize_prompt = (
            f"<{_context_tag}>\n"
            f"{indent(context)}\n"
            f"</{_context_tag}>\n"
            f"\n"
            f"<{_content_tag}>\n"
            f"{indent(content)}\n"
            f"</{_content_tag}>\n"
            f"\n"
            f"Any information provided in the outermost `{_context_tag}` tag is known. "
            f"Take this into account when summarizing the text in the outermost `{_content_tag}` tag."
        )

        message = {"role": "user", "content": summarize_prompt}
        try:
            response_message = openai.ChatCompletion.create(*args, messages=[message], **kwargs)
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
        recap: str = "[conversation did not start yet]",
        max_instruction_len: int = 1_000,
        min_data_len: int = 10,
        _recap_tag: str = "Recap",
        _data_tag: str = "Data",
        **kwargs: any) -> Response:

    len_instruction = len(instruction)
    if len_instruction >= max_instruction_len:
        raise ValueError(f"Instruction too long: {len_instruction} >= {max_instruction_len}")

    if data is None:
        data_prompt = ""

    else:
        data_prompt = (
            f"<{_data_tag}>\n"
            f"{indent(data)}\n"
            f"</{_data_tag}>\n"
            f"\n"
        )
    while True:
        prompt = (
            f"<{_recap_tag}>\n"
            f"{indent(recap)}\n"
            f"</{_recap_tag}>\n"
            f"\n"
            f"{data_prompt}"
            f"{instruction}"
        )

        messages = [{"role": "user", "content": prompt}]
        try:
            response_message = openai.ChatCompletion.create(*args, messages=messages, **kwargs)
            first_choice, = response_message.choices
            first_message = first_choice.message
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


def run_dialog() -> None:
    text = (
        "ausgelöste hohe Inflation und der wachsende Druck für deutliche Lohnerhöhungen erforderten ein "
        "ungewöhnliches Maß an Mobilisierung unter den Gewerkschaftsmitgliedern.ieser Kontext stellte "
        "sowohl für die Arbeitnehmer- als auch für die Arbeitgeberseite eine noch nie dagewesene "
        "Herausforderung dar und erforderte neuartige Ansätze, um die notwendige Kraft zu mobilisieren."
    )

    instructions = "What is the text about?"

    response = respond(instructions, data=text, model="gpt-3.5-turbo")
    print(response)


def run_summarize() -> None:
    text = extract_text("/home/mark/Downloads/2308.10379.pdf")
    summary = summarize(text, model="gpt-3.5-turbo")
    print(summary)


def main() -> None:
    openai.api_key_path = "resources/openai_api_key.txt"

    # run_dialog()
    run_summarize()


if __name__ == "__main__":
    main()
