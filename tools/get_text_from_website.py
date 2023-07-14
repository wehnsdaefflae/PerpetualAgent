# coding=utf-8
import time

from bs4 import BeautifulSoup, Comment
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from tools.summarize_text import summarize_text


def get_text_from_website(url: str, len_summary: int | None = None) -> str:
    driver = webdriver.Chrome()
    # driver = webdriver.Chrome(executable_path=ChromeDriverManager().install())
    driver.get(url)

    # Wait for the page to load
    time.sleep(5)  # Adjust this value based on the complexity of the website or your internet speed

    # Retrieve the page source and parse it with BeautifulSoup
    html: str = driver.page_source
    soup: BeautifulSoup = BeautifulSoup(html, 'html.parser')

    # Find and extract all visible text
    texts: list[str] = soup.findAll(text=True)

    def visible_text(element: any) -> bool:
        if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
            return False
        elif isinstance(element, Comment):
            return False
        return True

    visible_texts: list[str] = list(filter(visible_text, texts))

    text: str = ' '.join(t.strip() for t in visible_texts)

    if len_summary is None:
        return text

    return summarize_text(text, len_summary)
