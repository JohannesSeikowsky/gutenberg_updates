# Finds Wikipedia links for authors using Perplexity. 
# Perplexity is an AI-based search engine. Kind of like a combination of Google search and an LLM.
# Be aware that many books have more than one author (including translators etc.).
# For each author who is not already on Gutenberg, we use Perplexity to search based on author name, life dates, and their book titles.
# Read the prompting for a better understanding.
# We're feeding in the other books by the author to give Perplexity more context to find the correct Wikipedia link.
# Results are validated in a basic way to avoid obvious mistakes.

import json
import requests
import time
from bs4 import BeautifulSoup
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()
perplexity_api = os.getenv("PERPLEXITY_API_KEY")

# Validate API key exists
if not perplexity_api:
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

    try:
        parts = life_dates.split('-', 1)  # Split on first dash only
        birth = parts[0].strip() if parts[0].strip().isnumeric() else None
        death = parts[1].strip() if len(parts) > 1 and parts[1].strip().isnumeric() else None


        return birth, death
    except (ValueError, IndexError) as e:
        print(f"Error parsing life dates '{life_dates}': {e}")
        return None, None


def use_perplexity(prompt):
    """Call Perplexity API."""
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [
            {
                "role": "system",
                "content": PERPLEXITY_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {perplexity_api}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Perplexity error: {e}")
        return "perplexity_error"


def perplexity_wiki_search(author_name, life_dates, titles):
    """Search for author Wikipedia link using Perplexity API.

    Args:
        author_name: Full name of author
        life_dates: Birth-death dates in format "YYYY-YYYY" or variants
        titles: List of book titles by this author

    Returns:
        Wikipedia URL or error message from Perplexity
    """
    birth, death = parse_life_dates(life_dates) if life_dates else (None, None)

    # Build prompt based on available information
    if birth and death:
        prompt = f"""Find the wikipedia link of {author_name} who lived {life_dates} if it exists. Make sure the year of birth and year of death match exactly. {NAME_MATCH_INSTRUCTIONS} {COMMON_INSTRUCTIONS}"""
    elif birth:
        prompt = f"""Find the wikipedia link of {author_name} who was born in {birth} if it exists. Make sure the year of birth matches exactly. {NAME_MATCH_INSTRUCTIONS} {COMMON_INSTRUCTIONS}"""
    elif death:
        prompt = f"""Find the wikipedia link of {author_name} who died in {death} if it exists. Make sure the year of death matches exactly. {NAME_MATCH_INSTRUCTIONS} {COMMON_INSTRUCTIONS}"""
    else:
        # No life dates available, search by titles
        print("No Life Dates.")
        if len(titles) == 1:
            prompt = f"""I am trying to find the wikipedia link of "{author_name}" who wrote this book or script:
  - {titles[0]}

Look for a wikipedia entry that has an exact name match with "{author_name}" (including middle names, if any exist) and that directly references the aforementioned work called "{titles[0]}" directly within its content.

Accept that first or middle names of the author may be abbreviated.

{COMMON_INSTRUCTIONS}"""
        else:
            titles_list = "\n  - " + "\n  - ".join(titles)
            prompt = f"""I am trying to find the wikipedia link of "{author_name}" who wrote these books or scripts:{titles_list}

Look for a wikipedia entry that has an exact name match with "{author_name}" (including middle names if any exist) and that directly references at least one of the aforementioned works directly within its content.

Accept that first or middle names of the author may be abbreviated.

{COMMON_INSTRUCTIONS}"""

    return use_perplexity(prompt)


def get_author_metadata(author_id):
    """Gets all book titles by the author (additional relevant info to feed into the Perplexity search)
    and checks whether the author already has a wikipedia link (to avoid duplication).
    """
    url = f"https://www.gutenberg.org/ebooks/author/{author_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; GutenbergAuthor/1.0; +https://github.com)'
    }
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get book titles
        li_tags = soup.find_all("li", class_="booklink")
        titles = [book.find("span", class_="title").text for book in li_tags]

        # Check if author already has Wikipedia link
        a_tags = soup.find_all("a")
        has_wiki_link = any("wikipedia.org" in str(link.get("href")) for link in a_tags)

        return {
            'book_titles': titles,
            'has_wiki_link': has_wiki_link
        }
    except requests.RequestException as e:
        print(f"Error fetching author metadata: {e}")
        return None


def exclude_already_done_authors(authors):
    """Exclude authors for which we've already tried to find a wikipedia link before."""
    with open("done_authors.txt", "r") as f:
        already_done = set(f.read().split("\n"))
    return [author for author in authors if author['id'] not in already_done]


def check_perplexity_answer(answer):
    """Validate that Perplexity answer is a legitimate Wikipedia page."""
    try:
        # Make sure answer is ONLY a wikipedia link (single URL)
        if len(answer.strip().split(" ")) != 1:
            return False

        # Strip anchor links but don't reject them
        clean_url = answer.split("#")[0] if "#" in answer else answer

        # Fetch page to verify it's not a "no article" page
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; GutenbergAuthor/1.0; +https://github.com)'}
        response = requests.get(clean_url, timeout=REQUEST_TIMEOUT, headers=headers)
        response.raise_for_status()

        # Check for "no article exists" messages in various languages
        if any(text in response.text for text in WIKIPEDIA_NOT_FOUND_TEXTS):
            return False

        return True
    except Exception as e:
        print(f"Validation error for {answer}: {e}")
        return False


def get_sub_url(wikipedia_link):
    """Extract subdomain from Wikipedia URL (e.g., 'en.wikipedia')."""
    return ".".join(wikipedia_link.split("/")[2].split(".")[:2])


def generate_sql(author_id, wikipedia_url):
    """Generate SQL INSERT statement for author Wikipedia link."""
    description = get_sub_url(wikipedia_url)
    return f"insert into author_urls (fk_authors, description, url) values ({author_id},'{description}','{wikipedia_url}');"


def save_author_wikipedia_link(author_id, wikipedia_link, results_file):
    """Append SQL statement to results file."""
    sql = generate_sql(author_id, wikipedia_link)
    with open(results_file, "a") as f:
        f.write(sql + "\n")


def record_author_as_done(author_id):
    """Mark author as processed in done_authors.txt."""
    with open("done_authors.txt", "a") as f:
        f.write(author_id + "\n")


def get_author_wikipedia_link(author, author_metadata):
    """Main function to find and validate Wikipedia link for an author."""
    author_name = author['name']
    life_dates = author['life_dates']
    titles = author_metadata['book_titles']

    perplexity_answer = perplexity_wiki_search(author_name, life_dates, titles)

    if check_perplexity_answer(perplexity_answer):
        return perplexity_answer
    return None