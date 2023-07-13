# coding=utf-8
import requests
from urllib import parse


def get_scientific_research_articles(query: str) -> list[dict[str, str]]:
    """Fetches a list of scientific research articles from Semantic Scholar API based on a provided search query.

    This function retrieves a list of scientific research articles based on a provided search query related to any scientific topic or keywords. The query searches the Semantic Scholar API database and returns detailed information about each found article. It is useful for users seeking detailed insights on research articles concerning a specific subject.

    Example:
        >>> get_scientific_research_articles("Artificial Intelligence")

    Args:
        query (str): A string containing the topic or keywords to search for in the scientific articles database.

    Returns:
        list[dict]: Returns a list of dictionaries where each dictionary contains detailed information about a particular article. Each dictionary includes the key "title" for the title of the article, and "paperID" for the Google Scholar ID of the article. If no articles are found, the function returns an empty list.
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
