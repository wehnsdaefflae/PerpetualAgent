# coding=utf-8
import logging
import time
from traceback import format_exc

import openai
from openai.openai_object import OpenAIObject
from sentence_transformers import SentenceTransformer
import tiktoken

from utils.logging_handler import logging_handlers

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handlers = logging_handlers()
for each_handler in handlers:
    logger.addHandler(each_handler)


def openai_chat_deprecated(function_id: str, ack: bool = True, *args: any, **kwargs: any) -> OpenAIObject:
    while True:
        for i in range(5):
            try:
                logger.info(f"Calling OpenAI API: {function_id}")
                logger.debug(f"OpenAI API: args={args}, kwargs={kwargs}")
                response = openai.ChatCompletion.create(*args, **kwargs)
                return response

            except Exception as e:
                msg = f"Error {e}. Retrying chat completion {i + 1} of 5"
                logger.error(msg)
                logger.debug(format_exc())
                time.sleep(1)
                continue

        if ack:
            input("Chat completion failed. Press enter to retry...")


def num_tokens_from_messages(messages: list[dict[str, any]], model: str = "gpt-3.5-turbo-0613") -> int:
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)

    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1

    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted

    elif "gpt-3.5-turbo" in model:
        print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")

    elif "gpt-4" in model:
        print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return num_tokens_from_messages(messages, model="gpt-4-0613")

    else:
        raise NotImplementedError(
            f"num_tokens_from_messages() is not implemented for model {model}. "
            f"See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."
        )

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def truncate_content(content: str, model_name: str, target_tokens: int, truncation_sign: str = "[...]") -> str:
    len_s = len(truncation_sign)
    encoding = tiktoken.encoding_for_model(model_name)
    for i in range(len(content)):
        if i < 1:
            truncated_content = content

        elif len_s >= i:
            continue

        else:
            truncated_content = f"{truncation_sign}{content[-i:]}"

        tokens = encoding.encode(truncated_content)
        if target_tokens >= len(tokens):
            return truncated_content

    return ""


def truncate_messages(token_limit: int, tokens_reserved: int, messages: list[dict[str, any]], model_name: str) -> list[dict[str, any]]:
    messages = messages.copy()
    adjusted_token_limit = token_limit - tokens_reserved
    message_tokens = num_tokens_from_messages(messages, model_name)
    too_much = max(message_tokens - adjusted_token_limit, 0)
    while 0 < too_much:
        logger.info(f"Truncating messages. Removing {too_much} tokens in total.")
        first_message = messages[0]
        tokens_in_message = num_tokens_from_messages([first_message], model_name)
        if tokens_in_message >= too_much:
            target_tokens = tokens_in_message - too_much
            truncated_content = truncate_content(first_message["content"], model_name, target_tokens)
            if len(truncated_content) < 1:
                messages.pop(0)
            else:
                first_message["content"] = truncated_content
            break

        else:
            messages.pop(0)

        message_tokens = num_tokens_from_messages(messages, model_name)
        too_much = max(message_tokens - adjusted_token_limit, 0)

    return messages


def openai_chat(function_id: str, tokens_reserved: int = 1_024, ack: bool = True, *args: any, **kwargs: any) -> OpenAIObject:
    token_limits = {  # https://platform.openai.com/docs/models/gpt-4
        "gpt-3.5-turbo-16k":        16_384,
        "gpt-3.5-turbo-16k-0613":   16_384,
        "gpt-4-32k-0613":           32_768,
        "gpt-4-0613":                8_192,
        "gpt-4":                     8_192,
        "gpt-3.5-turbo-0613":        4_096,
        "gpt-3.5-turbo":             4_096,
    }

    while True:
        for i in range(5):
            try:
                messages = kwargs.pop("messages")
                model = kwargs.pop("model")
                token_limit = token_limits[model]
                messages_truncated = truncate_messages(token_limit, tokens_reserved, messages, model_name=model)
                logger.info(f"Calling OpenAI API: {function_id}")
                response = openai.ChatCompletion.create(*args, messages=messages_truncated, model=model, **kwargs)
                return response

            except Exception as e:
                msg = f"Error {e}. Retrying chat completion {i + 1} of 5"
                logger.error(msg)
                logger.debug(format_exc())
                time.sleep(1)
                continue

        if ack:
            input("Chat completion failed. Press enter to retry...")


def _get_embeddings(segments: list[str]) -> list[list[float]]:
    # model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    model = SentenceTransformer("ggrn/e5-small-v2")
    embedding_numpy = model.encode(segments, show_progress_bar=False)
    embedding = embedding_numpy.tolist()
    return embedding


def get_embeddings(segments: list[str]) -> list[list[float]]:
    # todo: check this: https://www.youtube.com/watch?v=QdDoFfkVkcw
    model = "text-embedding-ada-002"  # max input tokens: 8191, dimensions: 1536
    # model = "text-similarity-davinci-001"
    # model = "text-similarity-curie-001"
    # model = "text-similarity-babbage-001"
    # model = "text-similarity-ada-001"

    while True:
        for i in range(5):
            try:
                result = openai.Embedding.create(
                    input=segments,
                    model=model,
                )
                return [record["embedding"] for record in result["data"]]

            except Exception as e:
                msg = f"Error {e}. Retrying embedding {i + 1} of 5"
                logger.error(format_exc())
                print(msg)
                time.sleep(1)
                continue

        input("Embedding retrieval failed. Press enter to retry...")


def print_stream(stream: OpenAIObject) -> str:
    full_content = list()
    for chunk in stream:
        delta = chunk["choices"][0]["delta"]
        msg = delta.get("content", "")
        full_content.append(msg)
        print(msg, end="")
    print()
    return "".join(full_content)
