# coding=utf-8
import json
from dataclasses import dataclass
import openai
import tiktoken
from pdfminer.high_level import extract_text

from utils.misc import segment_text


def get_max_tokens(model_name: str) -> int:
    model_tokens_mapping = {
        "gpt-4": 8_192,
        "gpt-4-0613": 8_192,
        "gpt-4-32k": 32_768,
        "gpt-4-32k-0613": 32_768,
        "gpt-4-0314": 8_192,
        "gpt-4-32k-0314": 32_768,
        "gpt-3.5-turbo": 4_097,
        "gpt-3.5-turbo-16k": 16_385,
        "gpt-3.5-turbo-0613": 4_097,
        "gpt-3.5-turbo-16k-0613": 16_385,
        "gpt-3.5-turbo-0301": 4_097,
        "text-davinci-003": 4_097,
        "text-davinci-002": 4_097,
        "code-davinci-002": 8_001,
        "babbage-002": 16_384,
        "davinci-002": 16_384
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


def indent(text: str, indent_str: str = "    ") -> str:
    return "\n".join(f"{indent_str}{line}" for line in text.splitlines())


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

    if context is None:
        instruction = f"Summarize the text in the outermost `{_content_tag}` tag. Do not mention the tag."

    else:
        instruction = (
            f"Summarize the text in the outermost `{_content_tag}` tag as a seamless continuation "
            f"of the text in the outermost `{_context_tag}` tag. Do not mention the tags."
        )

    if additional_instruction is not None:
        instruction += f" {additional_instruction.strip()}"

    prompt = (
        _make_element(context, _context_tag) +
        _make_element(content, _content_tag) +
        instruction
    )
    return prompt


def summarize(
        content: str,
        *args: any,
        context: str | None = None,
        additional_instruction: str | None = None,
        max_input_ratio: float = .7,
        segment_length: int = 2_000,
        _margin: float = .1,
        _content_tag: str = "Content",
        _context_tag: str = "Context",
        **kwargs: any) -> str:

    model_name = kwargs["model"]
    max_tokens = get_max_tokens(model_name)

    summarize_prompt = _summarize_prompt(content, context, additional_instruction, _content_tag, _context_tag)
    messages = [{"role": "user", "content": summarize_prompt}]
    len_tokenized_prompt = get_token_len(messages, model_name) * (1. + _margin)

    if max_input_ratio >= len_tokenized_prompt / max_tokens:
        response_message = openai.ChatCompletion.create(*args, messages=messages, **kwargs)
        first_choice, = response_message.choices
        first_message = first_choice.message
        output = first_message.content
        return output

    print("segmenting...")
    rolling_summary = None
    last_context = None
    summaries = list()
    segments = list(segment_text(content, segment_length=segment_length))
    for i, each_segment in enumerate(segments):
        print(f"segment {i + 1} of {len(segments)} segments")
        each_summary = summarize(
            each_segment,
            *args,
            # context=rolling_summary,
            context=last_context,
            additional_instruction=additional_instruction,
            max_input_ratio=max_input_ratio,
            segment_length=segment_length,
            _margin=_margin,
            _content_tag=_content_tag,
            _context_tag=_context_tag,
            **kwargs
        )

        if rolling_summary is None:
            rolling_summary = each_summary

        else:
            last_context = f"{rolling_summary.strip()}\n{each_segment.strip()}"
            rolling_summary = summarize(
                f"{rolling_summary.strip()}\n{each_summary.strip()}",
                *args,
                additional_instruction=additional_instruction,
                max_input_ratio=max_input_ratio,
                segment_length=segment_length,
                _margin=_margin,
                _content_tag=_content_tag,
                _context_tag=_context_tag,
                **kwargs
            )

        summaries.append(each_summary.strip())

    return "\n\n".join(summaries)


# output debug log


def _response_prompt(
        instruction: str,
        recap: str | None,
        data: str | None,
        _recap_tag: str, _data_tag: str,
        _instruction_tag: str = "Instruction") -> str:

    recap_element = _make_element(recap, _recap_tag)
    data_element = _make_element(data, _data_tag)
    instruction_element = _make_element(instruction.rstrip() + " (NOTE: Do not imitate the above XML syntax.)", _instruction_tag)

    prompt = (
            recap_element +
            data_element +
            instruction_element
    )

    return prompt


def respond(
        request: str, *args: any,
        data: str | None = None,
        recap: str | None = None,
        ratio_request: float = .1,
        ratio_recap: float = .3,
        ratio_data: float = .3,
        ratio_response: float = .3,
        _margin: float = .1,
        _recap_tag: str = "ConversationLog",
        _summary_tag: str = "ConversationSummary",
        _data_tag: str = "AdditionalData",
        **kwargs: any) -> Response:

    ratio_recap = 0. if recap is None else ratio_recap
    ratio_data = 0. if data is None else ratio_data

    sum_ratios = ratio_request + ratio_recap + ratio_data + ratio_response
    ratio_response_target = ratio_response / sum_ratios

    model_name = kwargs["model"]
    max_tokens = get_max_tokens(model_name)

    prompt = _response_prompt(request, recap, data, _recap_tag, _data_tag)
    messages = [{"role": "user", "content": prompt}]
    len_tokenized_prompt = get_token_len(messages, model_name) * (1. + _margin)

    while ratio_response_target < len_tokenized_prompt / max_tokens:
        sum_input_ratios = ratio_request + ratio_recap + ratio_data
        ratio_request_is = len(request) / len_tokenized_prompt
        ratio_request_delta = ratio_request_is - ratio_request / sum_input_ratios
        ratio_recap_is = 0. if recap is None else len(recap) / len_tokenized_prompt
        ratio_recap_delta = ratio_recap_is - ratio_recap / sum_input_ratios
        ratio_data_is = 0. if data is None else len(data) / len_tokenized_prompt
        ratio_data_delta = ratio_data_is - ratio_data / sum_input_ratios

        max_delta = max(ratio_request_delta, ratio_recap_delta, ratio_data_delta)

        if ratio_request_delta == max_delta:
            request = summarize(request, *args, context=recap, **kwargs)

        elif ratio_data_delta == max_delta:
            focus_instruction = f"Transcribe this into a more concise format. Ignore information that is not relevant to the request \"{request.strip()}\""
            data = summarize(data, *args, context=recap, additional_instructions=focus_instruction, **kwargs)

        else:
            focus_conversation = "Be very concise but preserve literal information and conversational character."
            recap_text = summarize(recap, *args, additional_instruction=focus_conversation, **kwargs)
            recap = _make_element(recap_text, _summary_tag)

        prompt = _response_prompt(request, recap, data, _recap_tag, _data_tag)
        messages = [{"role": "user", "content": prompt}]
        len_tokenized_prompt = get_token_len(messages, model_name) * (1. + _margin)

    response_message = openai.ChatCompletion.create(*args, messages=messages, **kwargs)
    first_choice, = response_message.choices
    first_message = first_choice.message
    output = first_message.content

    updated_recap_content = (
            (f"" if recap is None else recap) +
            _make_element(
                (f"" if data is None else _make_element(data.rstrip(), _data_tag)) +
                _make_element(request.rstrip(), "Instruction"),
                "UserRequest") +
            _make_element(output.rstrip(), "AssistantResponse")
    )
    return Response(output, updated_recap_content)


def run_dialog() -> None:
    summary = None
    while True:
        instructions = input("User: ")
        response = respond(instructions, model="gpt-3.5-turbo", recap=summary)
        output = response.output
        summary = response.summary
        print(f"Assistant: {output.rstrip()}")
        print()


def run_summarize() -> None:
    text = extract_text("/home/mark/Downloads/2308.10379.pdf")
    # text = extract_text("/home/mark/Downloads/About – __countercloud.pdf")

    summary = summarize(text, model="gpt-3.5-turbo")
    print(summary)


def main() -> None:
    openai.api_key_path = "resources/openai_api_key.txt"

    # run_dialog()
    run_summarize()


if __name__ == "__main__":
    main()
