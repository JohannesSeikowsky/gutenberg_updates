# Finds Wikipedia links for authors using Perplexity. 
# Perplexity is an AI-based search engine. Kind of like a combination of Google search and an LLM.
# Be aware that many books have more than one author (including translators etc.).
# For each author who is not already on Gutenberg, we use Perplexity to search based on author name, life dates, and their book titles.
# Read the prompting for a better understanding.
# We're feeding in the other books by the author to give Perplexity more context to find the correct Wikipedia link.
# Results are validated in a basic way to avoid obvious mistakes.

import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")

# Validate API key exists
if not perplexity_api_key:
    raise ValueError("PERPLEXITY_API_KEY not found in environment variables")

# Constants
PERPLEXITY_MODEL = "sonar-pro"
REQUEST_TIMEOUT = 10

PERPLEXITY_SYSTEM_PROMPT = """your job is to help me find the correct wikipedia link of a person I'm interested in. I will tell you what I know about that specific person. Then you'll search the web and try to find the right wikipedia link for that particular person if it exists. Make sure to only ever return ONE link to me if you find one for the person. Also make sure it's the wikipedia of the actual person him- or herself, not the wikipedia of the NAME per se or a disambiguation page or a list of some kind. Especially make sure it's NOT a wikipedia page that says that there is no wikipedia entry about that person! I am ONLY interested in the wikipedia entry that is centrally about that person and tells me something about him or her! So please only ever give me such a link if you can find it. If you can find one return only the wikipedia link. If you can not find it, return 'not found."""

# Common prompt parts for deduplication
COMMON_INSTRUCTIONS = """If you can find the correct link for this person, return ONLY the wikipedia link, nothing else! If you can not find a link for this person, return only the phrase 'not found.'. Please note that we're only interested in wikipedia entries that are either in English or in the native language of the author."""

NAME_MATCH_INSTRUCTIONS = "Also make sure the name is an exact match (including middle names if any exist). However accept that first or middle names may be abbreviated."

WIKIPEDIA_NOT_FOUND_TEXTS = [
    "Wikipedia does not have an article with this exact name",
    "Soit vous avez mal écrit le titre",
    "В Википедии нет статьи с таким названием.",
    "Wikipedia todavía no tiene una página llamada",
    "Dieser Artikel existiert nicht.",
    "Wikipedia in lingua italiana non ha ancora una voce con questo nome.",
    "Wikipediassa ei ole tämän nimistä artikkelia.",
    "Wikipedia heeft geen artikel met de naam",
    "Svenskspråkiga Wikipedia har ännu inte någon sida med namnet"
]


def parse_life_dates(life_dates):
    """Parse life dates string into (birth_year, death_year) tuple."""
    if not life_dates or '-' not in life_dates:
        return None, None

    parts = life_dates.split('-', 1)
    birth_year = parts[0].strip() if parts[0].strip().isdigit() else None
    death_year = parts[1].strip() if len(parts) > 1 and parts[1].strip().isdigit() else None
    return birth_year, death_year


def extract_wikipedia_subdomain(wikipedia_url):
    """Extract subdomain from Wikipedia URL (e.g., 'en.wikipedia')."""
    return ".".join(wikipedia_url.split("/")[2].split(".")[:2])


def query_perplexity_api(prompt):
    """Call Perplexity API with given prompt and return response."""
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [
            {"role": "system", "content": PERPLEXITY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception:
        return "perplexity_error"


def search_author_wikipedia(author_name, life_dates, book_titles):
    """Search for author Wikipedia link using Perplexity API."""
    birth_year, death_year = parse_life_dates(life_dates) if life_dates else (None, None)

    if birth_year and death_year:
        prompt = f"Find the wikipedia link of {author_name} who lived {life_dates} if it exists. Make sure the year of birth and year of death match exactly. {NAME_MATCH_INSTRUCTIONS} {COMMON_INSTRUCTIONS}"
    elif birth_year:
        prompt = f"Find the wikipedia link of {author_name} who was born in {birth_year} if it exists. Make sure the year of birth matches exactly. {NAME_MATCH_INSTRUCTIONS} {COMMON_INSTRUCTIONS}"
    elif death_year:
        prompt = f"Find the wikipedia link of {author_name} who died in {death_year} if it exists. Make sure the year of death matches exactly. {NAME_MATCH_INSTRUCTIONS} {COMMON_INSTRUCTIONS}"
    else:
        work_type = "book or script" if len(book_titles) == 1 else "books or scripts"
        reference_phrase = f'the aforementioned work called "{book_titles[0]}"' if len(book_titles) == 1 else "at least one of the aforementioned works"
        titles_list = f"\n  - {book_titles[0]}" if len(book_titles) == 1 else "\n  - " + "\n  - ".join(book_titles)

        prompt = f"""I am trying to find the wikipedia link of "{author_name}" who wrote these {work_type}:{titles_list}

Look for a wikipedia entry that has an exact name match with "{author_name}" (including middle names if any exist) and that directly references {reference_phrase} directly within its content.

Accept that first or middle names of the author may be abbreviated.

{COMMON_INSTRUCTIONS}"""

    return query_perplexity_api(prompt)


def get_author_metadata(author_id):
    """Fetch book titles and check if author already has Wikipedia link."""
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; GutenbergAuthor/1.0; +https://github.com)'}
    try:
        response = requests.get(
            f"https://www.gutenberg.org/ebooks/author/{author_id}",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        titles = [book.find("span", class_="title").text for book in soup.find_all("li", class_="booklink")]
        has_wiki_link = any("wikipedia.org" in (link.get("href", "")) for link in soup.find_all("a"))

        return {'book_titles': titles, 'has_wiki_link': has_wiki_link}
    except requests.RequestException:
        return None


def is_valid_wikipedia_page(url):
    """Validate that URL is a legitimate Wikipedia page."""
    if not url or len(url.strip().split()) != 1:
        return False

    try:
        clean_url = url.split("#")[0]
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; GutenbergAuthor/1.0; +https://github.com)'}
        response = requests.get(clean_url, timeout=REQUEST_TIMEOUT, headers=headers)
        response.raise_for_status()

        return not any(text in response.text for text in WIKIPEDIA_NOT_FOUND_TEXTS)
    except Exception:
        return False


def save_author_wiki_sql(author_id, wikipedia_url, results_file):
    """Append SQL statement to results file."""
    wikipedia_subdomain = extract_wikipedia_subdomain(wikipedia_url)
    insert_statement = f"insert into author_urls (fk_authors, description, url) values ({author_id},'{wikipedia_subdomain}','{wikipedia_url}');"
    with open(results_file, "a") as f:
        f.write(insert_statement + "\n")


def get_author_wikipedia_link(author, author_metadata):
    """Find and validate Wikipedia link for an author."""
    print(f"  Searching for {author['name']}...")
    wikipedia_url = search_author_wikipedia(
        author['name'],
        author['life_dates'],
        author_metadata['book_titles']
    )
    return wikipedia_url if is_valid_wikipedia_page(wikipedia_url) else None