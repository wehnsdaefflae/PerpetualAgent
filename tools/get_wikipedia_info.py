# coding=utf-8
import wikipedia


def get_wikipedia_info(wikipedia_page_name: str) -> str:
    """
    Get more information about a topic from Wikipedia.

    Example:
        >>> get_wikipedia_info("Django")

    Args:
        wikipedia_page_name (str): the name of the wikipedia article.

    Returns:
        str: a summary of the topic.
    """
    try:
        return wikipedia.summary(wikipedia_page_name, auto_suggest=False)
    except wikipedia.exceptions.DisambiguationError as e:
        options = "\n".join(f"- {each_option}" for each_option in e.options)
        return f"Please specify your query by picking one of the following options:\n{options}"
    except wikipedia.exceptions.PageError:
        suggestion = wikipedia.suggest(wikipedia_page_name)
        if suggestion is None:
            return "Sorry, I could not find any information about this topic."
        return f"Did you mean {suggestion}? {wikipedia.summary(suggestion)}"
