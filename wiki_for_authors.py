# Finds Wikipedia links for authors using Perplexity.
# For each author who isn't already on Gutenberg, we use Perplexity to search based on author name, life dates, and their book titles.
# Perplexity is a search engine that uses AI to search the web.
# Results are validated to ensure they're actual Wikipedia pages before saving.

import json
import requests
import time
from bs4 import BeautifulSoup
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()
perplexity_api = os.getenv("PERPLEXITY_API_KEY")


def life_dates_check(life_dates):
    "separate the different cases for life dates"
    try:
        life_dates = life_dates.split("-")
        if life_dates[0].isnumeric() and life_dates[1].isnumeric():
            return "complete"
        if life_dates[0].isnumeric():
            return "only_birth"
        if life_dates[1].isnumeric():
            return "only_death"
    except:
        return "complete"


def use_perplexity(prompt):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": """your job is to help me find the correct wikipedia link of a person I'm interested in. I will tell you what I know about that specific person. Then you'll search the web and try to find the right wikipedia link for that particular person if it exists. Make sure to only ever return ONE link to me if you find one for the person. Also make sure it's the wikipedia of the actual person him- or herself, not the wikipedia of the NAME per se or a disambiguation page or a list of some kind. Especially make sure it's NOT a wikipedia page that says that there is no wikipedia entry about that person! I am ONLY interested in the wikipedia entry that is centrally about that person and tells me something about him or her! So please only ever give me such a link if you can find it. If you can find one return only the wikipedia link. If you can not find it, return 'not found."""
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
        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(e)
        return "perplexity_error"


def perplexity_wiki_search(author_name, life_dates, titles):
    if life_dates:
        # record life dates
        # print("Life dates: ", life_dates)

        # do perplexity search
        if life_dates_check(life_dates) == "complete":
            prompt = f"""Find the wikipedia link of {author_name} who lived {life_dates} if it exists. Make sure the year of birth and year of death match exactly. Also make sure the name is an exact match (including middle names if any exist). However accept that first or middle names may be abbreviated. If you can find the correct link for this person, return ONLY the wikipedia link, nothing else! If you can not find a link for this perwson, return only the phrase 'not found.'. Please note that we're only interested in wikipedia entries that are either in English or in the native language of the author."""
        elif life_dates_check(life_dates) == "only_birth":
            life_dates = life_dates.split("-")[0]
            prompt = f"""Find the wikipedia link of {author_name} who was born in {life_dates} if it exists. Make sure the year of birth matches exactly. Also make sure the name is an exact match (including middle names if any exist). However accept that first or middle names may be abbreviated. If you can find the correct link for this person, return ONLY the wikipedia link, nothing else! If you can not find a link for this perwson, return only the phrase 'not found.'. Please note that we're only interested in wikipedia entries that are either in English or in the native language of the author."""
        elif life_dates_check(life_dates) == "only_death":
            life_dates = life_dates.split("-")[1]
            prompt = f"""Find the wikipedia link of {author_name} who died in {life_dates} if it exists. Make sure the year of death matches exactly. Also make sure the name is an exact match (including middle names if any exist). However accept that first or middle names may be abbreviated. If you can find the correct link for this person, return ONLY the wikipedia link, nothing else! If you can not find a link for this perwson, return only the phrase 'not found.'. Please note that we're only interested in wikipedia entries that are either in English or in the native language of the author."""
    else:
        print("No Life Dates.")
        if len(titles) == 1:
            # if only one titles on Gutenberg
            prompt = f"""I am trying to find the wikipedia link of "{author_name}" who wrote this book or script:
  - {titles[0]}

  Look for a wikipedia entry that has an exact name match with "{author_name}" (including middle names,if any exist) and that directly references the aforementioned work called "{titles[0]}" directly within its content.

  Accept that first or middle names of the author may be abbreviated.

  If you can find a wikipedia entry that fits these criteria, return ONLY that wikipedia link, nothing else! If you can not find it, return only the phrase 'not found.'. Please note that we're only interested in wikipedia entries that are either in English or in the native language of the author."""
        else:
            # if more than one title on Gutenberg
            titles = "\n-".join(titles)
            prompt = f"""I am trying to find the wikipedia link of "{author_name}" who wrote these books or scripts:
  - {titles}

  Look for a wikipedia entry that has an exact name match with "{author_name}" (including middle names if any exist) and that directly references at least one of the aforementioned works directly within its content.

  Accept that first or middle names of the author may be abbreviated.

  If you can find a wikipedia entry that fits these criteria, return ONLY that wikipedia link, nothing else! If you can not find it, return only the phrase 'not found.'. Please note that we're only interested in wikipedia entries that are either in English or in the native language of the author."""
    # print(prompt)
    perplexity_answer = use_perplexity(prompt)
    return perplexity_answer


def get_author_metadata(author_id):
    """
    Fetch author metadata in one request.
    Returns dict with: book_titles, has_wiki_link
    """
    url = f"https://www.gutenberg.org/ebooks/author/{author_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; GutenbergAuthor/1.0; +https://github.com)'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        # Get book titles
        li_tags = soup.find_all("li", class_="booklink")
        titles = [book.find("span", class_="title").text for book in li_tags]

        # Check if author already has Wikipedia link
        a_tags = soup.find_all("a")
        has_wiki_link = any("wikipedia.org" in str(a.get("href")) for a in a_tags)

        return {
            'book_titles': titles,
            'has_wiki_link': has_wiki_link
        }
    except requests.RequestException as e:
        print(f"Error fetching author metadata: {e}")
        return None


def exclude_already_done_authors(authors):
    "exclude authors that have already been done (i.e. have an entry in done_authors.txt)"
    with open("done_authors.txt", "r") as f:
        already_done = f.read().split("\n")
    not_done = []
    for author in authors:
        if list(author.keys())[0] not in already_done:
            not_done.append(author)
    return not_done


def check_perplexity_answer(answer):
    "exclude perplexity answers that are obviously wrong."
    try:
        # make sure answer is ONLY a wikipedia link
        if len(answer.strip().split(" ")) != 1:
            return False
        if "#" in answer:
            return False
        # Make sure it's not a Wikipedia page that says there is no page like this
        no_wiki_text = ["Wikipedia does not have an article with this exact name", "Soit vous avez mal écrit le titre", "В Википедии нет статьи с таким названием.", "Wikipedia todavía no tiene una página llamada", "Dieser Artikel existiert nicht.", "Wikipedia in lingua italiana non ha ancora una voce con questo nome.", "Wikipediassa ei ole tämän nimistä artikkelia.", "Wikipedia heeft geen artikel met de naam", "Svenskspråkiga Wikipedia har ännu inte någon sida med namnet"]
        if any(text in requests.get(answer).text for text in no_wiki_text):
            return False
        return True
    except:
      return True


def get_sub_url(wikipedia_link):
    "gets en.wikipedia etc. from a wikipedia link"
    return ".".join(wikipedia_link.split("/")[2].split(".")[:2])


def generate_sql(author_id, perplexity_answer):
    description = get_sub_url(perplexity_answer)
    sql = f"insert into author_urls (fk_authors, description, url) values ({author_id},'{description}','{perplexity_answer}');"
    return sql


def save_author_wikipedia_links(author_id, wikipedia_link, results_file):
    sql = generate_sql(author_id, wikipedia_link)
    with open(results_file, "a") as f:
        f.write(sql + "\n")


def record_author_as_done(author_id):
    with open("done_authors.txt", "a") as f:
        f.write(author_id + "\n")


def get_author_wikipedia_links(authors, results_file):
    """
    Find Wikipedia links for authors.
    authors: list of author dicts from get_book_metadata()
    """
    # Convert to old format for compatibility with exclude_already_done_authors
    authors_old_format = []
    for author in authors:
        author_id = author['id']
        name = author['name']
        life_dates = author['life_dates']
        authors_old_format.append({author_id: [name, life_dates]})

    authors_old_format = exclude_already_done_authors(authors_old_format)
    if not authors_old_format:
        print("Author Wikis already done for all authors.")

    # Note - A book can have more than one author.
    for author in authors_old_format:
        author_id = list(author.keys())[0]
        author_name = list(author.values())[0][0]
        life_dates = list(author.values())[0][1]

        # Get author metadata (titles and wiki status) in one call
        author_metadata = get_author_metadata(author_id)
        if not author_metadata:
            print(f"Author Wikis: Error fetching metadata for {author_id}")
            record_author_as_done(author_id)
            continue

        if not author_metadata['has_wiki_link']:
            titles = author_metadata['book_titles']
            perplexity_answer = perplexity_wiki_search(author_name, life_dates, titles)
            print("Author Wikis: ", perplexity_answer)
            if check_perplexity_answer(perplexity_answer):
                save_author_wikipedia_links(author_id, perplexity_answer, results_file)
        else:
            print("Author Wikis already on Gutenberg.")
        record_author_as_done(author_id)


