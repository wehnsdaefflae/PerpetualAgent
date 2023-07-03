# coding=utf-8
import logging
import time
from traceback import format_exc

import openai
from openai.openai_object import OpenAIObject
from sentence_transformers import SentenceTransformer

from utils.logging_handler import logging_handlers

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handlers = logging_handlers()
for each_handler in handlers:
    logger.addHandler(each_handler)


def openai_chat(function_id: str, *args: any, **kwargs: any) -> OpenAIObject:
    while True:
        for i in range(5):
            try:
                logger.info(f"Calling OpenAI API: {function_id}")
                logger.debug(f"OpenAI API: args={args}, kwargs={kwargs}")
                response = openai.ChatCompletion.create(*args, **kwargs)
                return response

            except Exception as e:
                msg = f"Error {e}. Retrying chat completion {i + 1} of 5"
                logger.error(str(format_exc()))
                print(msg)
                time.sleep(1)
                continue

        input("Chat completion failed. Press enter to retry...")


def get_embeddings(segments: list[str]) -> list[list[float]]:
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embedding_numpy = model.encode(segments)
    embedding = embedding_numpy.tolist()
    return embedding


def _get_embeddings(segments: list[str]) -> list[list[float]]:
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
