# coding=utf-8
import wikipedia


def get_wikipedia_info(wikipedia_page_name: str) -> str:
    """Retrieves a summary of a specified Wikipedia page.

    This function fetches a concise summary of a desired Wikipedia article, given its title. If the specified article leads to a disambiguation page, the function returns a list of potential options for the user to further specify their search. In case the specified page does not exist, it either suggests a similar existing page or alerts the user if there's no related page available.

    Example:
        >>> get_wikipedia_info("Python (programming language)")

    Args:
        wikipedia_page_name (str): The title of the Wikipedia article from which the summary is to be retrieved.

    Returns:
        str: A string containing the summary of the Wikipedia page if it exists. If the specified page leads to a disambiguation page, a list of potential matches is returned. In the event that the page does not exist, the function either suggests a similar page or notifies the user if no suitable alternative can be found.
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
