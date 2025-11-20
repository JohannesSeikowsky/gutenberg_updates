# Finds Wikipedia links for books
# We use Serper (Google search API) to search for wikipedia links related to the book.
# Then we use ChatGPT to filter for those wikipedia link(s) that are actually about the book (not about the author or a film or whatnot)
# For non-English books, we search for both the English and the native language Wikipedia pages.

from utils import *
import json
import wikipedia
import urllib.parse
from pydantic import BaseModel
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def confirm_wikipedia_page(book_title, content, language=None):
    """Uses GPT to verify if Wikipedia matches the given book."""
    class Choice(BaseModel):
        correct_wikipedia_page: bool

    articles_to_avoid = """    <articles_to_avoid>
      - wikipedia article of the author (rather than the book)"""

    if language:
        articles_to_avoid += f"""
      - wikipedia article that are not in {language} (the language of the book or script)"""

    articles_to_avoid += """
      - wikipedia article of a film
    </articles_to_avoid>"""

    system_prompt = """Firstly you will be given the title of a book or script, then you'll be given an excerpt from a wikipedia article. Your job is to read that excerpt very closely and decide whether the wikipedia article from which it's taken is the actual wikipedia article of the books or script whose name you were initially given."""
    prompt1 = f"""I'm searching for the wikipedia article of a particular book or script. Firstly I will give you the name of that book or script and it's author (if available). Then I will give you an excerpt from a wikipedia article I've found. Your job is to read that excerpt VERY carefully and based on your reading decide whether the wikipedia article from which it's taken is the actual Wikipedia article of the book or script I will have told you about.
    It is possible that in the tille of the book I will give you it well specify what Volumne of the work it is, like for example "Faust - Volume 1" or something similar or in the language of the book. In those cases ignore what volume it is and just focus on finding the right wikipedia of the book in general.

    There are also some common types of wikipedia article that I'd like you to avoid:
{articles_to_avoid}

    Instead I am ONLY looking for the wikipedia article of the book or script ITSELF! Please return correct_wikipedia_page as "True" if the wikipedia article I'll show you is the correct one in your opinion. If it's not the correct one, return correct_wikipedia_page as "False". Do you understand?"""
    prompt2 = """Yes! What is the name of the book or script whose wikipedia article you are looking for?"""
    prompt3 = f"""Ok. Now please provide me with an excerpt from a wikipedia article. I will read the excerpt carefully and based on my reading decide whether the wikipedia article it's taken from is the wikipedia article of: '{book_title}'"""

    completion = client.beta.chat.completions.parse(
        model="gpt-5",
        messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": prompt1}, {"role": "assistant", "content": prompt2}, {"role": "user", "content": book_title}, {"role": "assistant", "content": prompt3}, {"role": "user", "content": content}],
        response_format=Choice,
    )

    return completion.choices[0].message.parsed.correct_wikipedia_page


def google_search_with_serper(query):
    """Searches Google via Serper API and returns list of URLs."""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": 20})
    headers = {'X-API-KEY': os.getenv("SERPER_API_KEY"), 'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return [result["link"] for result in json.loads(response.text)["organic"]]


def get_wikipedia_summary(url):
    """Fetches Wikipedia summary from URL using the wikipedia library."""
    url = urllib.parse.unquote(url)
    language = url.split("/")[2].split(".")[0]
    wikipedia.set_lang(language)
    page_title = url.split('/wiki/')[-1].replace('_', ' ')
    return wikipedia.summary(page_title, auto_suggest=False)


def find_match(urls, title, language=None):
    """Checks URLs sequentially and returns the first Wikipedia page that gets confirmed as the correct one."""
    for url in urls:
        try:
            content = get_wikipedia_summary(url)
            if confirm_wikipedia_page(title, content, language):
                return url
        except Exception as e:
            print(f"Error checking URL {url}: {e}")
    return None


def get_book_wikipedia_links(title, language):
    """Finds and validates Wikipedia links for a book in English and native language."""
    # All urls found via Google search
    urls = google_search_with_serper(title + " wikipedia")

    # Filter to Wikipedia URLs and exclude unwanted types
    wikipedia_urls = [url for url in urls if "wikipedia.org" in url
                      and "simple." not in url and "File:" not in url
                      and "/Category:" not in url and "(disambiguation)" not in url]

    # Split into English and non-English
    english_urls = [url for url in wikipedia_urls if "https://en.wikipedia.org/" in url]
    non_english_urls = [url for url in wikipedia_urls if "https://en.wikipedia.org/" not in url]

    results = []

    # Check English Wikipedia
    english_match = find_match(english_urls, title)
    if english_match:
        results.append(english_match)

    # Check non-English Wikipedia if book is not in English
    if language != "English":
        non_english_match = find_match(non_english_urls, title, language)
        if non_english_match:
            results.append(non_english_match)

    return results


def save_book_wikis(book_id, urls, file):
    """Writes Wikipedia URLs as SQL INSERT statement to results file."""
    if urls:
        urls_str = " ".join(urls)
        sql = f"insert into attributes (fk_books,fk_attriblist,text,nonfiling) values ({book_id},500,'{urls_str}',0);"
        with open(file, 'a') as f:
            f.write(f"{sql}\n")