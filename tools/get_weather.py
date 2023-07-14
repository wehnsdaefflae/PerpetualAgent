from urllib.parse import quote
from tools.get_text_from_website import get_text_from_website


def get_weather(city: str, country: str) -> str:
    url = f"https://www.google.com/search?q=weather+{quote(city)}+{quote(country)}"
    weather_info = get_text_from_website(url)
    return weather_info
