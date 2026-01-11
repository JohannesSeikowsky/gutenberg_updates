# Finds Wikipedia links for books
# We use Serper (Google search API) to search for wikipedia links related to the book.
# Then we validate using Claude against full article content (first 3000 chars) using book title + authors.
# Validation stops at the first match per language set (English, then native language).
# For non-English books, we search for both the English and the native language Wikipedia pages.

import re
import anthropic
import requests
import os
from dotenv import load_dotenv
from utils import download_wikipedia_article

load_dotenv()
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


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


def validate_with_claude(wiki_url, title, authors_str):
    """Validate if Wikipedia article matches the book using Claude on full content."""
    try:
        validation_length = 3000
        content = download_wikipedia_article(wiki_url)[:validation_length]

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            system="You are a specialist at evaluating whether a certain Wikipedia article belongs to a specific literary work.",
            messages=[{
                "role": "user",
                "content": f"""I would like to check whether a particular Wikipedia article is the correct one for a literary work I've found online on Project Gutenberg. Here is some basic information about the work taken from Project Gutenberg, followed by the first 3000 characters of the Wikipedia article.

WORK (basic info):
- Title: {title}
- Author(s): {authors_str}

WIKIPEDIA ARTICLE (first 3000 characters):
```
{content}
```

In your opinion is this Wikipedia article the correct one for the WORK in question?
- Ignore edition details (translations, volumes, annotations)
- We are NOT interested in Wikipedia articles of the author, of movies based on the work or anything else. We are only interested in the Wikipedia article of the literary work itself.

Respond:
VERDICT: [YES/NO]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASONING: [one very short sentence]"""
            }]
        )

        answer = response.content[0].text
        verdict_match = re.search(r'VERDICT:\s*(YES|NO)', answer, re.IGNORECASE)
        result = verdict_match and verdict_match.group(1).upper() == "YES"
        return result

    except Exception:
        return False


def filter_wikipedia_urls(search_results):
    """Filter search results to valid Wikipedia article URLs."""
    unwanted_patterns = ["simple.", "File:", "/Category:", "(disambiguation)"]
    return [
        url for url in search_results
        if "wikipedia.org" in url and not any(pattern in url for pattern in unwanted_patterns)
    ]


def find_first_matching_url(urls, book_title, authors_str, language_label):
    """Check URLs and return first match, or None."""
    if not urls:
        return None

    for url in urls:
        if validate_with_claude(url, book_title, authors_str):
            return url
    return None


def get_book_wikipedia_links(book_title, book_language, authors_str):
    """Finds and validates Wikipedia links for book in English and native language using Claude."""
    print("  Searching and validating Wikipedia links...")
    search_results = google_search_with_serper(f"{book_title} wikipedia")
    wiki_urls = filter_wikipedia_urls(search_results)

    english_wiki_urls = [url for url in wiki_urls if url.startswith("https://en.wikipedia.org/")]
    native_wiki_urls = [url for url in wiki_urls if not url.startswith("https://en.wikipedia.org/")]

    validated_urls = []

    # Check English URLs first
    if english_match := find_first_matching_url(english_wiki_urls, book_title, authors_str, "English"):
        validated_urls.append(english_match)

    # Check native language URLs if book is not English
    if book_language != "English":
        if native_match := find_first_matching_url(native_wiki_urls, book_title, authors_str, book_language):
            validated_urls.append(native_match)

    return validated_urls


def save_book_wikis_sql(book_id, wiki_urls, output_file):
    """Appends SQL INSERT for Wikipedia URLs to results file."""
    if not wiki_urls:
        return
    urls_str = " ".join(wiki_urls)
    sql = f"insert into attributes (fk_books,fk_attriblist,text,nonfiling) values ({book_id},500,'{urls_str}',0);\n"
    with open(output_file, 'a') as f:
        f.write(sql)