# Finds Wikipedia links for books
# We use Serper (Google search API) to search for wikipedia links related to the book.
# Then we validate using two layers:
#   Layer 1 (GPT): Validates against Wikipedia summaries to confirm the page is about the book itself (not author articles, film adaptations, etc.)
#   Layer 2 (Claude): Deep validation against full article content (first 3000 chars) using book title + authors
# For non-English books, we search for both the English and the native language Wikipedia pages.

import wikipedia
import urllib.parse
import re
from pydantic import BaseModel
from openai import OpenAI
import anthropic
import requests
import os
from dotenv import load_dotenv
from utils import download_wikipedia_article

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
        model="gpt-5.2",
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


def validate_with_claude(wiki_url, title, authors_str):
    """Validate if Wikipedia article matches the book using Claude on full content."""
    try:
        validation_length = 3000
        content = download_wikipedia_article(wiki_url)[:validation_length]

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Does this Wikipedia article match the work listed below?

WORK:
- Title: {title}
- Author(s): {authors_str}

WIKIPEDIA ARTICLE (first 3000 chars):
```
{content}
```

Is the Wikipedia article about this work? Ignore edition details (translations, volumes, annotations).

Respond:
VERDICT: [YES/NO]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASONING: [one very short sentence]"""
            }]
        )

        answer = response.content[0].text
        verdict_match = re.search(r'VERDICT:\s*(YES|NO)', answer, re.IGNORECASE)
        return verdict_match and verdict_match.group(1).upper() == "YES"

    except Exception:
        return False


def get_book_wikipedia_links(book_title, book_language, authors_str):
    """Finds and validates Wikipedia links for book in English and native language using two-layer validation."""
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

    # Layer 2: Claude validation on full content
    validated_urls = []
    for url in matched_urls:
        if validate_with_claude(url, book_title, authors_str):
            validated_urls.append(url)
    return validated_urls


def save_book_wikis_sql(book_id, wiki_urls, output_file):
    """Appends SQL INSERT for Wikipedia URLs to results file."""
    if not wiki_urls:
        return
    urls_str = " ".join(wiki_urls)
    sql = f"insert into attributes (fk_books,fk_attriblist,text,nonfiling) values ({book_id},500,'{urls_str}',0);\n"
    with open(output_file, 'a') as f:
        f.write(sql)