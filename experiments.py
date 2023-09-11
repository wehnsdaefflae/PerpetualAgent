# coding=utf-8
import json
from dataclasses import dataclass
import openai
import tiktoken
from pdfminer.high_level import extract_text

from utils.misc import segment_text


# in summary() return concat of summaries
# process(data, instruction), give ratios for data, instruction, and output
# make summary use process
# make Conversation class with exchange history, give ratios for recap, instruction, and output
#  use summary to reduce post positive deviant from target distribution


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
    summaries = list()
    segments = list(segment_text(content, segment_length=segment_length))
    for i, each_segment in enumerate(segments):
        print(f"segment {i + 1} of {len(segments)} segments")
        if rolling_summary is None:
            each_summary = summarize(
                each_segment,
                *args,
                additional_instruction=additional_instruction,
                max_input_ratio=max_input_ratio,
                segment_length=segment_length,
                _margin=_margin,
                _content_tag=_content_tag,
                _context_tag=_context_tag,
                **kwargs
            )
            rolling_summary = each_summary

        else:
            each_summary = summarize(
                each_segment,
                *args,
                context=rolling_summary,
                additional_instruction=additional_instruction,
                max_input_ratio=max_input_ratio,
                segment_length=segment_length,
                _margin=_margin,
                _content_tag=_content_tag,
                _context_tag=_context_tag,
                **kwargs
            )
            rolling_summary = summarize(
                f"{rolling_summary}\n{each_summary}",
                *args,
                additional_instruction=additional_instruction,
                max_input_ratio=max_input_ratio,
                segment_length=segment_length,
                _margin=_margin,
                _content_tag=_content_tag,
                _context_tag=_context_tag,
                **kwargs
            )

        if len(each_summary) >= segment_length and i < len(segments) - 1:
            raise ValueError(f"Summary is longer {len(each_summary)} than segment length {segment_length}.")

        summaries.append(each_summary.strip())

    return "\n\n".join(summaries)


# output debug log


class Conversation:
    def __init__(self, ratio_request: float | int = .3, ratio_recap: float | int = .3, ratio_response: float | int = .4) -> None:
        sum_ratios = ratio_request + ratio_recap + ratio_response
        self.ratio_request = sum_ratios / ratio_request
        self.ratio_recap = sum_ratios / ratio_recap
        self.ratio_response = sum_ratios / ratio_response

        self.recap = ""

    def _response_prompt(
            self,
            request: str,
            _recap_tag: str) -> str:

        recap_element = _make_element(self.recap, _recap_tag)

        prompt = (
                recap_element +
                request.rstrip()
        )
        return prompt

    def respond(
            self,
            request: str, *args: any,
            _margin: float = .1,
            _recap_tag: str = "ConversationLog",
            _summary_tag: str = "ConversationSummary",
            **kwargs: any) -> str:

        model_name = kwargs["model"]
        max_tokens = get_max_tokens(model_name)

        prompt = self._response_prompt(request, _recap_tag)
        messages = [{"role": "user", "content": prompt}]
        len_tokenized_prompt = get_token_len(messages, model_name) * (1. + _margin)

        if len_tokenized_prompt / max_tokens < self.ratio_response:
            response_message = openai.ChatCompletion.create(*args, messages=messages, **kwargs)
            first_choice, = response_message.choices
            first_message = first_choice.message
            output = first_message.content
            self.recap += _make_element(request, "UserRequest")
            self.recap += _make_element(output, "AssistantResponse")
            return output

        ratio_request_is = len(request) / len_tokenized_prompt
        ratio_request_delta = ratio_request_is - self.ratio_request
        ratio_recap_is = len(self.recap) / len_tokenized_prompt
        ratio_recap_delta = ratio_recap_is - self.ratio_recap

        if ratio_request_delta >= ratio_recap_delta:
            request = summarize(request, *args, context=self.recap, **kwargs)

        else:
            focus_conversation = "Be very concise but preserve literal information and conversational character."
            recap_text = summarize(self.recap, *args, additional_instruction=focus_conversation, **kwargs)
            self.recap = (
                    f"<{_summary_tag}>\n" +
                    f"{indent(recap_text.rstrip())}\n" +
                    f"</{_summary_tag}>"
            )

        output = self.respond(
            request, *args,
            _margin=_margin,
            _recap_tag=_recap_tag,
            _summary_tag=_summary_tag,
            **kwargs)

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

    # normalize ;)
    sum_ratios = ratio_request + (0. if recap is None else ratio_recap) + (0. if data is None else ratio_data) + ratio_response
    ratio_request_target = ratio_request / sum_ratios
    ratio_recap_target = ratio_recap / sum_ratios
    ratio_data_target = ratio_data / sum_ratios
    ratio_response_target = ratio_response / sum_ratios

    model_name = kwargs["model"]
    max_tokens = get_max_tokens(model_name)

    prompt = _response_prompt(request, recap, data, _recap_tag, _data_tag)
    messages = [{"role": "user", "content": prompt}]
    len_tokenized_prompt = get_token_len(messages, model_name) * (1. + _margin)

    if len_tokenized_prompt / max_tokens < ratio_response_target:
        response_message = openai.ChatCompletion.create(*args, messages=messages, **kwargs)
        first_choice, = response_message.choices
        first_message = first_choice.message
        output = first_message.content

        updated_recap_content = (
                (f"" if recap is None else f"{recap}\n") +
                "<UserRequest>\n" +
                f"{indent(request).rstrip()}\n" +
                f"</UserRequest>\n" +
                f"\n" +
                f"<AssistantResponse>\n" +
                f"{indent(output).rstrip()}\n" +
                f"</AssistantResponse>"
        )

        return Response(output, updated_recap_content)

    print("condensing...")
    ratio_request_is = len(request) / len_tokenized_prompt
    ratio_request_delta = ratio_request_is - ratio_request_target
    ratio_recap_is = 0. if recap is None else len(recap) / len_tokenized_prompt
    ratio_recap_delta = ratio_recap_is - ratio_recap_target
    ratio_data_is = 0. if data is None else len(data) / len_tokenized_prompt
    ratio_data_delta = ratio_data_is - ratio_data_target

    max_delta = max(ratio_request_delta, ratio_recap_delta, ratio_data_delta)

    if ratio_request_delta == max_delta:
        request = summarize(request, *args, context=recap, **kwargs)

    elif ratio_recap_delta == max_delta:
        focus_conversation = "Be very concise but preserve literal information and conversational character."
        recap_text = summarize(recap, *args, additional_instruction=focus_conversation, **kwargs)
        recap = (
                f"<{_summary_tag}>\n" +
                f"{indent(recap_text.rstrip())}\n" +
                f"</{_summary_tag}>"
        )

    else:
        focus_instruction = f"Focus on information relevant to the following request: \"{request.strip()}\""
        data = summarize(data, *args, context=recap, additional_instructions=focus_instruction, **kwargs)

    response = respond(
        request, *args,
        data=data,
        recap=recap,
        ratio_request=ratio_request, ratio_recap=ratio_recap, ratio_data=ratio_data, ratio_response=ratio_response,
        _margin=_margin,
        _recap_tag=_recap_tag,
        _summary_tag=_summary_tag,
        _data_tag=_data_tag,
        **kwargs)

    return response




def _process_prompt(
        instruction: str,
        data: str | None,
        _data_tag: str) -> str:
    data_element = _make_element(data, _data_tag)

    prompt = (
            data_element +
            instruction.rstrip()
    )
    return prompt


def process(
        instruction: str, *args: any,
        data: str | None = None,
        ratio_instruction: float | int = .1,
        ratio_data: float | int = .5,
        ratio_response: float | int = .4,
        _margin: float = .1,
        _data_tag: str = "AdditionalData",
        **kwargs: any) -> str:

    # normalize ;)
    sum_ratios = ratio_instruction + ratio_data + ratio_response
    ratio_instruction_target = ratio_instruction / sum_ratios
    ratio_data_target = ratio_data / sum_ratios
    ratio_response_target = ratio_response / sum_ratios

    model_name = kwargs["model"]
    max_tokens = get_max_tokens(model_name)

    prompt = _process_prompt(instruction, data, _data_tag)
    messages = [{"role": "user", "content": prompt}]
    len_tokenized_prompt = get_token_len(messages, model_name) * (1. + _margin)

    if len_tokenized_prompt / max_tokens < ratio_response_target:
        response_message = openai.ChatCompletion.create(*args, messages=messages, **kwargs)
        first_choice, = response_message.choices
        first_message = first_choice.message
        output = first_message.content
        return output

    print("condensing...")
    len_instruction = len(instruction)
    len_data = 0 if data is None else len(data)

    ratio_instruction_is = len_instruction / len_tokenized_prompt
    ratio_instruction_delta = ratio_instruction_is - ratio_instruction_target
    ratio_data_is = len_data / len_tokenized_prompt
    ratio_data_delta = ratio_data_is - ratio_data_target

    if ratio_data_delta < ratio_instruction_delta:
        instruction = summarize(instruction, *args, **kwargs)

    else:
        focus_instruction = f"Focus on information relevant to the following request: \"{instruction.strip()}\""
        data = summarize(data, *args, additional_instructions=focus_instruction, **kwargs)

    output = process(
        instruction, *args,
        data=data,
        ratio_instruction=ratio_instruction, ratio_data=ratio_data, ratio_response=ratio_response,
        _margin=_margin, _data_tag=_data_tag, **kwargs)

    return output


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

    # run_dialog()
    run_summarize()


if __name__ == "__main__":
    main()
