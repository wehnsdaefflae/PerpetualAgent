# coding=utf-8
import requests
from urllib import parse


def get_scientific_research_articles(query: str) -> list[dict[str, str]]:
    """
    Fetches a list of scientific research articles based on a provided search query from the Semantic Scholar API. The query
    can be any topic or keyword related to scientific research articles. The function is applicable in cases where users need
    to retrieve information about research articles for a specific subject.

    Example:
        >>> get_scientific_research_articles("Artificial Intelligence")

    Args:
        query (str): The topic or keywords to search for in the database of scientific articles.

    Returns:
        list[dict]: A list of dictionaries with information about each article. Each dictionary contains details such as title,
        authors, abstract, etc. If no articles are found, returns an empty list.
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
