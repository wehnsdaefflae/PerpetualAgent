# coding=utf-8
import logging
import time
from traceback import format_exc

import openai
from openai.openai_object import OpenAIObject

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


if __name__ == "__main__":
    text = ("In Meno, Plato's character (and old teacher) Socrates is challenged by Meno to explain how someone could find out what the nature of virtue is if they did not "
            "already know anything about it.[1] In other words, one who knows none of the attributes, properties, and/or other descriptive markers of any kind that help "
            "signify what something is (physical or otherwise) will not recognize it even after coming across it. Therefore, if the converse is true, and one knows the "
            "attributes, properties and/or other descriptive markers of this thing, one should not need to seek it out at all. The conclusion is that in either instance, "
            "there is no point trying to gain that \"something\"; in the case of Plato's aforementioned work, there is no point in seeking knowledge.\n"
            "\n"
            "Socrates' response is to develop his theory of anamnesis and to suggest that the soul is immortal, and repeatedly incarnated; knowledge is in the soul from "
            "eternity (86b), but each time the soul is incarnated its knowledge is forgotten in the trauma of birth. What one perceives to be learning, then, "
            "is the recovery of what one has forgotten. (Once it has been brought back it is true belief, to be turned into genuine knowledge by understanding.) Socrates (and "
            "Plato) thus sees himself not as a teacher but as a midwife, aiding with the birth of knowledge that was already there in the student.\n"
            "\n"
            "The theory is illustrated by Socrates asking a slave boy questions about geometry. At first, the boy gives the wrong answer; when that is pointed out to him, "
            "he is puzzled, but by asking questions, Socrates helps him to reach the correct answer. That is intended to show that since the boy was not told the answer, "
            "he reached the truth by only recollecting what he had once known but later forgotten.")

    words = list()
    for each_word in text.split():
        if each_word[0].lower() == "a":
            words.append(each_word)

    print(", ".join(words))

    content_following = (
        f"List all the words in the following text that start with the letter 'a'.\n"
        f"\n"
        f"{text}"
    )

    content_above = (
        f"{text}\n"
        f"\n"
        f"List all the words in the above text that start with the letter 'a'."
    )

    messages = [
        {
            "role": "user",
            "content": content_following
        }
    ]

    openai.api_key_path = "../resources/openai_api_key.txt"

    reply = openai_chat(
        "test_function",
        model="gpt-3.5-turbo",
        messages=messages)

    reply_message = reply["choices"][0]["message"]["content"]

    print("\nInstruction first (assumed better):")
    print(reply_message)

    messages = [
        {
            "role": "user",
            "content": content_above
        }
    ]

    reply = openai_chat(
        "test_function",
        model="gpt-3.5-turbo",
        messages=messages)

    reply_message = reply["choices"][0]["message"]["content"]

    print("\nContent first (assumed worse):")
    print(reply_message)
