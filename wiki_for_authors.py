# 
import json
import requests
import time
from bs4 import BeautifulSoup
import urllib.parse
from perplexity import use_perplexity, perplexity_wiki_search


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


