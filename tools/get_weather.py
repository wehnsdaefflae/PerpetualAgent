from urllib.parse import quote
from tools.get_text_from_website import get_text_from_website


def get_weather(city: str, country: str) -> str:
    """Retrieves current weather information for a specified city and country using Google's weather service.

    This function obtains the latest weather conditions for any city-country combination, provided that Google offers weather data for the specified location. It is designed to be universally applicable across all supported locales.

    Example:
        >>> get_weather("London", "United Kingdom")

    Args:
        city (str): The city for which the weather conditions are to be retrieved.
        country (str): The country in which the specified city is situated.

    Returns:
        str: A comprehensive string detailing the current weather conditions in the given city, using data from Google's weather service.
    """
    url = f"https://www.google.com/search?q=weather+{quote(city)}+{quote(country)}"
    weather_info = get_text_from_website(url)
    return weather_info
