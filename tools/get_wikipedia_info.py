# coding=utf-8
import wikipedia


def get_wikipedia_info(wikipedia_page_name: str) -> str:
    """
    This function retrieves a brief summary of a specified Wikipedia page.

    Example:
        >>> get_wikipedia_info("Python (programming language)")

    Args:
        wikipedia_page_name (str): The title of the desired Wikipedia article.

    Returns:
        str: If the specified page exists, a string containing the summary of that Wikipedia page is returned.
        In case of a disambiguation page, a list of possible options is returned for further specification.
        If the page does not exist, the function suggests a similar existing page or notifies the user if no similar page can be found.
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
