# coding=utf-8
import requests
from urllib import parse


def get_scientific_research_articles(query: str) -> list[dict[str, str]]:
    """
    Get scientific research articles from the Semantic Scholar API.

    Example:
        >>> get_scientific_research_articles("machine learning")

    Args:
        query (str): the search query.

    Returns:
        list[dict]: a list of dictionaries containing information about the articles.
    """

    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={parse.quote_plus(query)}"
    # url = f"https://api.semanticscholar.org/graph/v1/paper/search"
    #params = {
    #    "query": query,
    #    "sort": "relevance",
    #    "limit": 10,
    #}
    # response = requests.get(url, params=params)
    response = requests.get(url)

    if response.status_code != 200:
        return [{f"Request failed with status code {response.status_code}": response.text}]

    result = response.json()

    papers = result.get("data")
    if papers is None or len(papers) < 1:
        return []
    return papers
