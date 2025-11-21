# Finds Wikipedia links for books
# We use Serper (Google search API) to search for wikipedia links related to the book.
# Then we use ChatGPT to filter for those wikipedia link(s) that are actually about the book (not about the author or a film or whatnot)
# For non-English books, we search for both the English and the native language Wikipedia pages.

import wikipedia
import urllib.parse
from pydantic import BaseModel
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def google_search_with_serper(query):
    """Searches Google via Serper API and returns list of URLs."""
    headers = {
        'X-API-KEY': os.getenv("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    }
    response = requests.post(
        "https://google.serper.dev/search",
        headers=headers,
        json={"q": query, "num": 20}
    )
    return [result["link"] for result in response.json()["organic"]]


def get_wikipedia_summary(url):
    """Extracts Wikipedia page summary from URL."""
    decoded_url = urllib.parse.unquote(url)
    language = decoded_url.split("/")[2].split(".")[0]
    page_title = decoded_url.split('/wiki/')[-1].replace('_', ' ')
    wikipedia.set_lang(language)
    return wikipedia.summary(page_title, auto_suggest=False)


def confirm_wikipedia_page(book_title, wiki_excerpt, required_language=None):
    """Uses GPT to verify if Wikipedia article matches the book."""
    class Choice(BaseModel):
        correct_wikipedia_page: bool

    exclusions = ["author articles", "film adaptations"]
    if required_language:
        exclusions.append(f"non-{required_language} articles")

    exclusions_text = "\n".join(f"- {item}" for item in exclusions)

    system_prompt = "You verify whether a Wikipedia article excerpt matches a specific book or script title."

    user_prompt = f"""Determine if this Wikipedia excerpt is for the book itself (not {', '.join(exclusions)}).
Book title: {book_title}
Note: Ignore volume numbers in titles (e.g., "Faust - Volume 1" → match general "Faust" article).

Wikipedia excerpt:
{wiki_excerpt}

Return correct_wikipedia_page: true if this is the book's Wikipedia article, false otherwise."""

    completion = client.beta.chat.completions.parse(
        model="gpt-5",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=Choice,
    )

    return completion.choices[0].message.parsed.correct_wikipedia_page


def find_matching_wikipedia_page(candidate_urls, book_title, required_language=None):
    """Returns first URL confirmed to be the book's Wikipedia page."""
    for url in candidate_urls:
        try:
            wiki_excerpt = get_wikipedia_summary(url)
            if confirm_wikipedia_page(book_title, wiki_excerpt, required_language):
                return url
        except Exception as e:
            print(f"Error checking {url}: {e}")
    return None


def get_book_wikipedia_links(book_title, book_language):
    """Finds Wikipedia links for book in English and native language."""
    search_results = google_search_with_serper(f"{book_title} wikipedia")

    unwanted_url_patterns = ["simple.", "File:", "/Category:", "(disambiguation)"]
    wiki_urls = [
        url for url in search_results
        if "wikipedia.org" in url and not any(pattern in url for pattern in unwanted_url_patterns)
    ]

    english_wiki_urls = [url for url in wiki_urls if url.startswith("https://en.wikipedia.org/")]
    native_wiki_urls = [url for url in wiki_urls if not url.startswith("https://en.wikipedia.org/")]

    matched_urls = []
    if english_match := find_matching_wikipedia_page(english_wiki_urls, book_title):
        matched_urls.append(english_match)

    if book_language != "English" and (native_match := find_matching_wikipedia_page(native_wiki_urls, book_title, book_language)):
        matched_urls.append(native_match)

    return matched_urls


def save_book_wikis_sql(book_id, wiki_urls, output_file):
    """Appends SQL INSERT for Wikipedia URLs to results file."""
    if not wiki_urls:
        return
    urls_str = " ".join(wiki_urls)
    sql = f"insert into attributes (fk_books,fk_attriblist,text,nonfiling) values ({book_id},500,'{urls_str}',0);\n"
    with open(output_file, 'a') as f:
        f.write(sql)