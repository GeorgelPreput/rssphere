"""Scrape web pages using Selenium and Chrome driver."""

import contextlib
import importlib.resources as pkg_res
import random
import time

import html2text
import toml
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

with pkg_res.open_text("rssphere.scraper", "config.toml") as config_file:
    config = toml.load(config_file)

    HEADLESS_OPTIONS = config["HEADLESS_OPTIONS"]
    USER_AGENTS = config["USER_AGENTS"]


def setup_selenium() -> WebDriver:
    """Set up Selenium.

    Returns
    -------
    WebDriver
        Configured WebDriver object to use for scraping.

    """
    options = Options()

    user_agent: str = random.choice(USER_AGENTS)  # noqa: S311
    options.add_argument(f"user-agent={user_agent}")

    for option in HEADLESS_OPTIONS:
        options.add_argument(option)

    service = Service(r"./.venv/bin/chromedriver")

    return Chrome(service=service, options=options)  # pyright: ignore[reportCallIssue]


def accept_cookies(driver: WebDriver) -> None:
    """Try to find and click on a cookie consent button. It looks for several common patterns.

    Parameters
    ----------
    driver : WebDriver
        Selenium WebDriver object to use for scraping.

    """
    with contextlib.suppress(Exception):
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//button | //a | //div")),
        )

        for tag in ["button", "a", "div"]:
            for text in [
                "accept",
                "agree",
                "allow",
                "consent",
                "continue",
                "ok",
                "I agree",
                "got it",
            ]:
                with contextlib.suppress(NoSuchElementException):
                    element = driver.find_element(
                        By.XPATH,
                        f"""
                        //{tag}[contains(translate(
                            text(),
                            'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                            'abcdefghijklmnopqrstuvwxyz'
                        ), '{text}')]""",
                    )
                    if element:
                        element.click()


def fetch_html_selenium(url: str) -> str:
    """Scrape raw HTML of a web page using Selenium.

    Parameters
    ----------
    url : str
        URL of the web page to be scraped.

    Returns
    -------
    str
        HTML code of scraped page.

    """
    driver = setup_selenium()
    try:
        driver.get(url)

        time.sleep(random.randint(1, 2))  # noqa: S311
        driver.maximize_window()

        accept_cookies(driver)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        return driver.page_source
    finally:
        driver.quit()


def clean_html(html_content: str) -> str:
    """Clean HTML content by removing headers and footers based on common HTML tags or classes.

    Parameters
    ----------
    html_content : str
        Raw HTML content to be cleaned.

    Returns
    -------
    str
        Cleaned HTML content.

    """
    soup = BeautifulSoup(html_content, "html.parser")

    for element in soup.find_all(["header", "footer"]):
        element.decompose()

    return soup.prettify()


def html_to_markdown(html_content: str) -> str:
    """Convert raw HTML content to Markdown using the Readability library.

    Parameters
    ----------
    html_content : str
        Raw HTML content to be converted to Markdown.

    Returns
    -------
    str
        Markdown content.

    """
    cleaned_html = clean_html(html_content)

    markdown_converter = html2text.HTML2Text()
    markdown_converter.ignore_links = False

    return markdown_converter.handle(cleaned_html)


def get_web_page(url: str) -> str:
    """Get HTML content of a web page, converted to Markdown format.

    Parameters
    ----------
    url : str
        URL of the web page to be scraped.

    Returns
    -------
    str
        Scraped page as Markdown.

    """
    raw_content = fetch_html_selenium(url)

    return html_to_markdown(raw_content)
