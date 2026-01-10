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
    print(f"    Checking: {wiki_url}")
    try:
        validation_length = 3000
        content = download_wikipedia_article(wiki_url)[:validation_length]
        print(f"      Downloaded article: {len(content)} chars")

        response = anthropic_client.messages.create(
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
        print(f"      Claude response:\n{answer}")
        verdict_match = re.search(r'VERDICT:\s*(YES|NO)', answer, re.IGNORECASE)
        result = verdict_match and verdict_match.group(1).upper() == "YES"
        print(f"      Validation result: {result}")
        return result

    except Exception as e:
        print(f"      Error during validation: {e}")
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

    print(f"  Checking {language_label} URLs...")
    for url in urls:
        if validate_with_claude(url, book_title, authors_str):
            print(f"  ✓ {language_label} match found: {url}")
            return url
        else:
            print(f"  ✗ Not a match: {url}")

    print(f"  ✗ No {language_label} URLs validated")
    return None


def get_book_wikipedia_links(book_title, book_language, authors_str):
    """Finds and validates Wikipedia links for book in English and native language using Claude."""
    search_results = google_search_with_serper(f"{book_title} wikipedia")
    print(f"  Serper: Found {len(search_results)} total URLs")

    wiki_urls = filter_wikipedia_urls(search_results)
    print(f"  Filtered to {len(wiki_urls)} Wikipedia URLs")

    english_wiki_urls = [url for url in wiki_urls if url.startswith("https://en.wikipedia.org/")]
    native_wiki_urls = [url for url in wiki_urls if not url.startswith("https://en.wikipedia.org/")]
    print(f"    - English URLs: {len(english_wiki_urls)}")
    print(f"    - Native language URLs: {len(native_wiki_urls)}")

    validated_urls = []

    # Check English URLs first
    if english_match := find_first_matching_url(english_wiki_urls, book_title, authors_str, "English"):
        validated_urls.append(english_match)

    # Check native language URLs if book is not English
    if book_language != "English":
        if native_match := find_first_matching_url(native_wiki_urls, book_title, authors_str, book_language):
            validated_urls.append(native_match)

    if validated_urls:
        print(f"  Final: {len(validated_urls)} validated URL(s)")
    else:
        print(f"  Final: No URLs validated")

    return validated_urls


def save_book_wikis_sql(book_id, wiki_urls, output_file):
    """Appends SQL INSERT for Wikipedia URLs to results file."""
    if not wiki_urls:
        return
    urls_str = " ".join(wiki_urls)
    sql = f"insert into attributes (fk_books,fk_attriblist,text,nonfiling) values ({book_id},500,'{urls_str}',0);\n"
    with open(output_file, 'a') as f:
        f.write(sql)