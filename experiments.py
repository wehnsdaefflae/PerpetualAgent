# coding=utf-8
import json
from dataclasses import dataclass
import openai
import tiktoken
from pdfminer.high_level import extract_text

from utils.misc import segment_text


def get_max_tokens(model_name: str) -> int:
    model_tokens_mapping = {
        "gpt-4":                     8_192,
        "gpt-4-0613":                8_192,
        "gpt-4-32k":                32_768,
        "gpt-4-32k-0613":           32_768,
        "gpt-4-0314":                8_192,
        "gpt-4-32k-0314":           32_768,
        "gpt-3.5-turbo":             4_097,
        "gpt-3.5-turbo-16k":        16_385,
        "gpt-3.5-turbo-0613":        4_097,
        "gpt-3.5-turbo-16k-0613":   16_385,
        "gpt-3.5-turbo-0301":        4_097,
        "text-davinci-003":          4_097,
        "text-davinci-002":          4_097,
        "code-davinci-002":          8_001,
        "babbage-002":              16_384,
        "davinci-002":              16_384
    }

    return model_tokens_mapping[model_name]


def _make_element(content: str | None, _tag_name: str) -> str:
    if content is None:
        return ""

    return (
        f"<{_tag_name}>\n"
        f"{indent(content).rstrip()}\n"
        f"</{_tag_name}>\n"
        f"\n"
    )


def get_token_len(messages: list[dict[str, str]], model_name: str) -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    messages_json = json.dumps(messages)
    tokenized_prompt = encoding.encode(messages_json)
    len_tokenized_prompt = len(tokenized_prompt)
    return len_tokenized_prompt


def indent(text: str, indent_str: str = "    ", times: int = 1) -> str:
    return "\n".join(f"{indent_str * times}{line}" for line in text.splitlines())


@dataclass(frozen=True)
class Response:
    output: str
    summary: str

    def __str__(self) -> str:
        return f"Response(output='{self.output}', summary='{self.summary}')"


def _summarize_prompt(
        content: str,
        context: str | None,
        additional_instruction: str | None,
        _content_tag: str, _context_tag: str) -> str:

    context_element = _make_element(context, _context_tag)
    if len(context_element) >= 1:
        instruction = f"Summarize the text in the outermost `{_content_tag}` tag."

    else:
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
    return summarize_prompt


def summarize(
        content: str,
        *args: any,
        context: str | None = None,
        additional_instruction: str | None = None,
        reserved_response_ratio: float = .5,
        segment_length: int = 2_000,
        model_name: str = "gpt-3.5-turbo",
        _margin: float = .1,
        _content_tag: str = "Content",
        _context_tag: str = "Context",
        **kwargs: any) -> str:

    max_tokens = get_max_tokens(model_name)

    summarize_prompt = _summarize_prompt(content, context, additional_instruction, _content_tag, _context_tag)
    messages = [{"role": "user", "content": summarize_prompt}]
    len_tokenized_prompt = get_token_len(messages, model_name) * (1. + _margin)

    while len_tokenized_prompt / max_tokens >= reserved_response_ratio:
        print("too much, segmenting")
        rolling_summary = None
        summaries = list()
        segments = list(segment_text(content, segment_length=segment_length))
        for i, each_segment in enumerate(segments):
            print(f"segment {i + 1} of {len(segments)} segments")
            if rolling_summary is None:
                each_summary = summarize(
                    each_segment,
                    *args,
                    model_name=model_name,
                    **kwargs
                )
                rolling_summary = each_summary

            else:
                each_summary = summarize(
                    each_segment,
                    *args,
                    context=rolling_summary,
                    model_name=model_name,
                    **kwargs
                )
                rolling_summary = summarize(f"{rolling_summary}\n{each_summary}", *args, model_name=model_name, **kwargs)

            summaries.append(each_summary)

        content = "\n".join(summaries)

        summarize_prompt = _summarize_prompt(content, context, additional_instruction, _content_tag, _context_tag)
        messages = [{"role": "user", "content": summarize_prompt}]
        len_tokenized_prompt = get_token_len(messages, model_name)

    response_message = openai.ChatCompletion.create(*args, model_name=model_name, messages=messages, **kwargs)
    first_choice, = response_message.choices
    first_message = first_choice.message
    output = first_message.content
    return output


def _response_prompt(
        instruction: str,
        recap: str | None,
        data: str | None,
        _recap_tag: str, _data_tag: str) -> str:

    recap_element = _make_element(recap, _recap_tag)
    data_element = _make_element(data, _data_tag)

    prompt = (
            recap_element +
            data_element +
            instruction.rstrip()
    )
    return prompt


def respond(
        instruction: str, *args: any,
        data: str | None = None,
        recap: str | None = None,
        model_name: str = "gpt-3.5-turbo",
        reserved_response_ratio: float = .5,
        _margin: float = .1,
        _recap_tag: str = "ConversationLog",
        _summary_tag: str = "ConversationSummary",
        _data_tag: str = "AdditionalData",
        **kwargs: any) -> Response:

    max_tokens = get_max_tokens(model_name)

    prompt = _response_prompt(instruction, recap, data, _recap_tag, _data_tag)
    messages = [{"role": "user", "content": prompt}]
    len_tokenized_prompt = get_token_len(messages, model_name) * (1. + _margin)

    while len_tokenized_prompt / max_tokens >= reserved_response_ratio:
        len_instruction = len(instruction)
        len_recap = -1 if recap is None else len(recap)
        len_data = -1 if data is None else len(data)

        if len_instruction >= len_data and len_instruction >= len_recap:
            instruction = summarize(instruction, *args, context=recap, model_name=model_name, **kwargs)

        elif len_recap >= len_instruction and len_recap >= len_data:
            focus_conversation = "Be very concise but preserve literal information and conversational character."
            recap_text = summarize(recap, *args, additional_instruction=focus_conversation, model_name=model_name, **kwargs)
            recap = (
                f"<{_summary_tag}>\n" +
                f"{indent(recap_text.rstrip())}\n" +
                f"</{_summary_tag}>"
            )

        elif len_data >= len_instruction and len_data >= len_recap:
            focus_instruction = f"Focus on information relevant to the following request: \"{instruction.strip()}\""
            data = summarize(data, *args, context=recap, additional_instructions=focus_instruction, model_name=model_name, **kwargs)

        else:
            raise ValueError(
                f"Undefined component lengths: "
                f"len_instruction {len_instruction}, len_recap {len_recap}, len_data {len_data}."
            )

        prompt = _response_prompt(instruction, recap, data, _recap_tag, _data_tag)
        messages = [{"role": "user", "content": prompt}]
        len_tokenized_prompt = get_token_len(messages, model_name)

    response_message = openai.ChatCompletion.create(*args, messages=messages, model_name=model_name, **kwargs)
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
