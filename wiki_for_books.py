# Finds Wikipedia links for books 
# We're using Serper (Google search API) to search for wikipedia links related to the book.
# Then we use ChatGPT to find the wikipedia link(s) that actually is about the book (not the author or a file or whatnot)  
# For non-English books, we searche for both English and native language Wikipedia pages.

from utils import *
import json
import wikipedia
import urllib.parse
import time
from pydantic import BaseModel
from openai import OpenAI
import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def check_english_wikipedia_page(book_title, content):
    "checks if the wikipedia page is about the book in question."
    class Choice(BaseModel):
        correct_wikipedia_page: bool

    system_prompt = """Firstly you will be given the title of a book or script, then you'll be given an excerpt from a wikipedia article. Your job is to read that excerpt very closely and decide whether the wikipedia article from which it's taken is the actual wikipedia article of the books or script whose name you were initially given."""
    prompt1 = f"""I'm searching for the wikipedia article of a particular book or script. Firstly I will give you the name of that book or script and it's author (if available). Then I will give you an excerpt from a wikipedia article I've found. Your job is to read that excerpt VERY carefully and based on your reading decide whether the wikipedia article from which it's taken is the actual Wikipedia article of the book or script I will have told you about.
    It is possible that in the tille of the book I will give you it well specify what Volumne of the work it is, like for example "Faust - Volume 1" or something similar or in the language of the book. In those cases ignore what volume it is and just focus on finding the right wikipedia of the book in general.

    There are also some common types of wikipedia article that I'd like you to avoid:
    <articles_to_avoid>
      - wikipedia article of the author (rather than the book)
      - wikipedia article of a film
    </articles_to_avoid>

    Instead I am ONLY looking for the wikipedia article of the book or script ITSELF! Please return correct_wikipedia_page as "True" if the wikipedia article I'll show you is the correct one in your opinion. If it's not the correct one, return correct_wikipedia_page as "False". Do you understand?"""
    prompt2 = """Yes! What is the name of the book or script whose wikipedia article you are looking for?"""
    prompt3 = f"""Ok. Now please provide me with an excerpt from a wikipedia article. I will read the excerpt carefully and based on my reading decide whether the wikipedia article it's taken from is the wikipedia article of: '{book_title}'"""

    completion = client.beta.chat.completions.parse(
        model="gpt-5",
        messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": prompt1}, {"role": "assistant", "content": prompt2}, {"role": "user", "content": book_title}, {"role": "assistant", "content": prompt3}, {"role": "user", "content": content}],
        response_format=Choice,
    )

    choice = completion.choices[0].message.parsed
    return choice.correct_wikipedia_page


def check_non_english_wikipedia_page(book_title, content, language):
    "checks if the wikipedia page is about the book in question."
    class Choice(BaseModel):
        correct_wikipedia_page: bool

    system_prompt = """Firstly you will be given the title of a book or script, then you'll be given an excerpt from a wikipedia article. Your job is to read that excerpt very closely and decide whether the wikipedia article from which it's taken is the actual wikipedia article of the books or script whose name you were initially given."""
    prompt1 = f"""I'm searching for the wikipedia article of a particular book or script. Firstly I will give you the name of that book or script and it's author (if available). Then I will give you an excerpt from a wikipedia article I've found. Your job is to read that excerpt VERY carefully and based on your reading decide whether the wikipedia article from which it's taken is the actual Wikipedia article of the book or script I will have told you about.
    It is possible that in the tille of the book I will give you it well specify what Volumne of the work it is, like for example "Faust - Volume 1" or something similar or in the language of the book. In those cases ignore what volume it is and just focus on finding the right wikipedia of the book in general.

    There are also some common types of wikipedia article that I'd like you to avoid:
    <articles_to_avoid>
      - wikipedia article of the author (rather than the book)
      - wikipedia article that are not in {language} (the language of the book or script)
      - wikipedia article of a film
    </articles_to_avoid>

    Instead I am ONLY looking for the wikipedia article of the book or script ITSELF! Please return correct_wikipedia_page as "True" if the wikipedia article I'll show you is the correct one in your opinion. If it's not the correct one, return correct_wikipedia_page as "False". Do you understand?"""
    prompt2 = """Yes! What is the name of the book or script whose wikipedia article you are looking for?"""
    prompt3 = f"""Ok. Now please provide me with an excerpt from a wikipedia article. I will read the excerpt carefully and based on my reading decide whether the wikipedia article it's taken from is the wikipedia article of: '{book_title}'"""

    completion = client.beta.chat.completions.parse(
        model="gpt-5",
        messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": prompt1}, {"role": "assistant", "content": prompt2}, {"role": "user", "content": book_title}, {"role": "assistant", "content": prompt3}, {"role": "user", "content": content}],
        response_format=Choice,
    )

    choice = completion.choices[0].message.parsed
    return choice.correct_wikipedia_page
  

def exclude_unwanted_links(links):
  return [link for link in links if "simple." not in link and "File:" not in link and "/Category:" not in link and "(disambiguation)" not in link]


def get_only_english_links(links):
  return [link for link in links if "https://en.wikipedia.org/" in link]


def get_non_english_links(links):
  return [link for link in links if "https://en.wikipedia.org/" not in link]


def get_wikipedia_summary(url):
  """Gets the first part of a Wikipedia article."""
  url = urllib.parse.unquote(url)
  language = url.split("/")[2].split(".")[0]
  wikipedia.set_lang(language)
  page_title = url.split('/wiki/')[-1].replace('_', ' ')
  page_content = wikipedia.summary(page_title, auto_suggest=False)
  return page_content


def save_results(book_id, title, urls, filename):
    data = { "book_id": book_id,
            "title_and_author": title,
            "urls": urls }
  
    with open(filename, 'a') as f:
        f.write(json.dumps(data) + '\n')


def record_error(error_message, log_file):
  with open(log_file, "a") as f:
      f.write(f"{error_message}\n\n")


def google_search_with_serper(query):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "num": 20 })

    headers = { 'X-API-KEY': os.getenv("SERPER_API_KEY"),
                'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text


def get_urls_from_search_results(search_results):
    urls = []
    results = json.loads(search_results)["organic"]
    for result in results:
        urls.append(result["link"])
    return urls


def get_book_wikipedia_links(title, language):
    # print(book_id, title)
    search_results = google_search_with_serper(title + " wikipedia")
    search_urls = get_urls_from_search_results(search_results)
    wikipedia_urls = [url for url in search_urls if "wikipedia.org" in url]
    urls = exclude_unwanted_links(wikipedia_urls)
    # print(urls)
    english_urls = get_only_english_links(wikipedia_urls)
    non_english_urls = get_non_english_links(wikipedia_urls)
    results = []
    
    for url in english_urls:
      # print("CHECKING ", url)
      try:
          content = get_wikipedia_summary(url)
          # print(content)
          is_english_wikipedia_page = check_english_wikipedia_page(title, content)
          if is_english_wikipedia_page:
              # print("yes")
              results.append(url)
              break
          else:
              pass
              # print("no")
      except Exception as e:
          print(f"Error for checking particular url")
          
    
    # If the book is not english, look for non-english wikipedia results
    if language != "English":
      for url in non_english_urls:
          # print("CHECKING ", url)
          try:
              content = get_wikipedia_summary(url)
              is_non_english_wikipedia_page = check_non_english_wikipedia_page(title, content, language)
              if is_non_english_wikipedia_page:
                  # print("yes")
                  results.append(url)
                  break
              else:
                  pass
          except Exception as e:
              print(f"Error for checking particular url")
        
    return results
    

def save_book_wikis(book_id, urls, file):
    # convert your results into sql queries (but exclude legacy links)
    if urls: # Exclude books without urls
        urls = " ".join(urls)
        sql = f"insert into attributes (fk_books,fk_attriblist,text,nonfiling) values ({book_id},500,'{urls}',0);"
        with open(file, 'a') as f:
            f.write(f"{sql}\n")