from typing import Dict
from tools.get_urls_from_google_query import get_urls_from_google_query
from tools.get_text_from_website import get_text_from_website

def gather_positions(search_term: str) -> Dict[str, str]:
    """
    Initiates a web search to gather information on diverse perspectives related to a specified topic.

    Example:
        >>> gather_positions("artificial consciousness")
        
    Args:
        search_term (str): The term or phrase that will be searched to gather divergent viewpoints.
        
    Returns:
        dict: A dictionary where each key-value pair represents a unique standpoint and the related information.
    """
    ret = dict()
    
    # Retrieve a list of URLs relevant to the search term
    urls = get_urls_from_google_query(search_term)

    for url in urls:
        # Generate summaries for each URL
        summary = get_text_from_website(url, len_summary=500)
        
        # Use the URL link as the unique standpoint and add the summary as the related info
        ret[url] = summary

    return ret