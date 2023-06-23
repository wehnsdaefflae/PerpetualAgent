from urllib.parse import quote
from tools.get_text_from_website import get_text_from_website

def get_weather(city: str, country: str) -> str:
    """
    Get the current weather condition for a given city and country from the Google weather site.

    Example:
        >>> weather = get_weather('Bamberg', 'Germany')

    Args:
        city (str): The name of the city for which to get the weather.
        country (str): The name of the country where the city is located.

    Returns:
        str: The current weather condition for the requested city and country.
    """
    url = f"https://www.google.com/search?q=weather+{quote(city)}+{quote(country)}"
    weather_info = get_text_from_website(url)
    return weather_info