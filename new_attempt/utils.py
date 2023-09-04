from abc import ABC, abstractmethod
from collections import namedtuple
from dataclasses import dataclass
from typing import TypeVar

import openai


class __DictableForwardRef(ABC):
    pass


D = TypeVar("D", bound=__DictableForwardRef)


class Dictable(__DictableForwardRef):
    @staticmethod
    @abstractmethod
    def from_dict(element_dict: dict[str, any]) -> D:
        raise NotImplementedError()

    @abstractmethod
    def to_dict(self) -> dict[str, any]:
        raise NotImplementedError()


def not_implemented(*args: any, **kwargs: any) -> any:
    raise NotImplementedError("must be set by controller")


@dataclass(frozen=True)
class ConversationResponse:
    response: str
    new_context: str | None = None


def call_llm(instructions: str, data: str | None = None, _context: str | None = None) -> ConversationResponse:
    def construct(_instructions: str, _data: str | None, __context: str | None) -> str:
        prompt_lines = list()
        if __context is not None:
            prompt_lines.append(
                "<PreviousConversation>\n"
                "context\n"
                "</PreviousConversation>\n"
                "\n"
            )

        if _data is not None:
            prompt_lines.append(
                "<AdditionalData>\n"
                "data\n"
                "</AdditionalData>\n"
                "\n"
            )

        prompt_lines.append(
            "<Instructions>\n"
            "instructions\n"
            "</Instructions>"
        )

        return "\n".join(prompt_lines)

    def summarize(_data: str) -> str:
        # summarize with llm
        return _data

    threshold = 1_000
    while True:
        prompt = construct(instructions, data, _context)
        try:
            response_message = openai.ChatCompletion.create(prompt=prompt, model="gpt-3.5-turbo")
            response = response_message.choices[0].content
            break

        except openai.error.OpenAIError as e:
            if e.code != "context window exceded":
                raise e

            if len(instructions) >= threshold:
                raise ValueError("Instructions very long. Consider moving info into `data`.")

            data = summarize(data)

    # doesnt work from here on
    exchange = (f"Conversation log:\n"
                f"{_context}\n"
                f"\n"
                f"Last exchange:\n"
                f""
                "")
    context_prompt = construct("Update the conversation log with the last exchange.", data, _context)
    new_summary = openai.Completion.create(prompt=context_prompt, model="gpt-3.5-turbo")

    return ConversationResponse(response=response, new_context=new_summary)