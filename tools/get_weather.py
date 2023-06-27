from urllib.parse import quote
from tools.get_text_from_website import get_text_from_website

def get_weather(city: str, country: str) -> str:
    """
    Retrieves the current weather information of a specified city in a specified country from Google's weather service. Suitable for general usage across all city-country combinations where Google provides weather data.

    Example:
        >>> get_weather("London", "United Kingdom")

    Args:
        city (str): The specific city for which to retrieve weather conditions.
        country (str): The country where the specified city is located.

    Returns:
        str: A string containing the current weather conditions in the given city, as provided by Google's weather service.
    """
    url = f"https://www.google.com/search?q=weather+{quote(city)}+{quote(country)}"
    weather_info = get_text_from_website(url)
    return weather_info
