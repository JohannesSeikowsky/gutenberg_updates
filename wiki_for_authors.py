# 
import json
import requests
import time
from bs4 import BeautifulSoup
import urllib.parse
from perplexity import use_perplexity, perplexity_wiki_search


def get_authors(book_id):
    "get the author of a book and his/her life dates if available"
    url = f"https://www.gutenberg.org/ebooks/{book_id}"
    r = requests.get(url).text
    soup = BeautifulSoup(r, 'html.parser')
    table = soup.find('table', class_='bibrec')
    table_rows = table.find_all('tr')
    
    titles = ["Author", "Editor", "Translator", "Illustrator", "Creator", "Commentator"]
    ids = []
    for row in table_rows:
        try:
            row_title = row.find("th").text
        except:
            continue
        if row_title in titles:
            author_id = row.find("td").find("a").get("href").split("/")[-1]
            author = row.find("td").find("a").text.strip()
            # separate life dates and name and format name.
            if any(char.isdigit() for char in author.split(", ")[-1]):
                life_dates = author.split(", ")[-1]
                author = author.split(", ")[:-1]
            else:
                author = author.split(", ")
                life_dates = None
            author = " ".join(reversed(author)) # format name - first name first
            if author_id.isnumeric():
                ids.append({author_id: [author, life_dates]})
    return ids


def get_book_titles(author_id):
    "get the titles of the works than an author has on Gutenberg"
    url = f"https://www.gutenberg.org/ebooks/author/{author_id}"
    r = requests.get(url)    
    re = BeautifulSoup(r.text, 'html.parser')
    li_tags = re.find_all("li", class_="booklink")
    titles = [book.find("span", class_="title").text for book in li_tags]
    return titles


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


def author_has_wiki(author_id):
    "check whether there already is a wikipedia page on gutenberg.org"
    url = f"https://www.gutenberg.org/ebooks/author/{author_id}"
    r = requests.get(url).text
    soup = BeautifulSoup(r, 'html.parser')
    a_tags = soup.find_all("a")
    if any("wikipedia.org" in str(a.get("href")) for a in a_tags):
      return True
    else:
      return False
        

def save_author_wikipedia_links(author_id, wikipedia_link, results_file):
    sql = generate_sql(author_id, wikipedia_link)
    with open(results_file, "a") as f:
        f.write(sql + "\n")


def record_author_as_done(author_id):
    with open("done_authors.txt", "a") as f:
        f.write(author_id + "\n")


def get_author_wikipedia_links(book_id, results_file):
    authors = get_authors(book_id)
    authors = exclude_already_done_authors(authors)
    if not authors:
        print("Author Wikis already done for all authors.")
    
    # Note - A book can have more than one author.
    for author in authors:
        author_id = list(author.keys())[0]
        author_name = list(author.values())[0][0]
        life_dates = list(author.values())[0][1]
        if not author_has_wiki(author_id):
            titles = get_book_titles(author_id)
    
            perplexity_answer = perplexity_wiki_search(author_name, life_dates, titles)
            print("Author Wikis: ", perplexity_answer)
            if check_perplexity_answer(perplexity_answer):
                save_author_wikipedia_links(author_id, perplexity_answer, results_file)
        else:
            print("Author Wikis already on Gutenberg.")
        record_author_as_done(author_id)


