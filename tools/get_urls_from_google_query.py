# coding=utf-8
import json

import requests


def get_urls_from_google_query(search_query: str) -> list[str]:
    """
    Retrieves a list of URLs relevant to a given search query based on Google's search results.

    This function can be used whenever there is a need to automate the process of getting search engine results. It is helpful when building systems that need to consume and analyze content from the web in response to a variety of search queries.

    Example:
        >>> get_urls_from_google_query("how to make a website")

    Args:
        search_query (str): The query to search in Google.

    Returns:
        list[str]: A list of URLs associated with the search query. If an error occurs, it returns a list containing a single string detailing the error.
    """
    with open("resources/configs/google.json", mode="r", encoding="utf-8") as f:
        config = json.load(f)

    api_key = config["google_api_key"]
    search_engine_id = config["search_engine_id"]

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": search_query,
        "key": api_key,
        "cx": search_engine_id,
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return [f"Request failed with status code {response.status_code}: {response.text}"]

    result = response.json()

    items = result.get("items")
    if items is None or len(items) < 1:
        return []
    return [each_item['link'] for each_item in items]
