from utils import *
import json
import wikipedia
import urllib.parse
import time
from pydantic import BaseModel
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import sys
client = OpenAI(api_key="REDACTED_API_KEY")


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
        model="gpt-4o",
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
        model="gpt-4o",
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


def get_title_and_language(book_id):
    url = f"https://www.gutenberg.org/ebooks/{book_id}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    content_div = soup.find('div', id='content')
    # get title
    title_tag = content_div.find('h1') if content_div else None
    title = title_tag.text.strip() if title_tag else "Title not found"
    # get language
    try:
        language = soup.find('table', class_='bibrec').find('th', text='Language').parent.find('td').text.strip()        
    except:
        language = "Not Found"
    return title, language


def google_search_with_serper(query):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "num": 20 })

    headers = { 'X-API-KEY': 'abcfe6ae08cbdb59fdf7aceec193a52855e912a1',
                'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text


def get_urls_from_search_results(search_results):
    urls = []
    results = json.loads(search_results)["organic"]
    for result in results:
        urls.append(result["link"])
    return urls




def get_wikipedia_links(book_id):
  try:
    # print(f"{book_id}")
    title, language = get_title_and_language(book_id)
    print(book_id, title)
    search_results = google_search_with_serper(title + " wikipedia")
    search_urls = get_urls_from_search_results(search_results)
    wikipedia_urls = [url for url in search_urls if "wikipedia.org" in url]
    urls = exclude_unwanted_links(wikipedia_urls)
    english_urls = get_only_english_links(wikipedia_urls)
    non_english_urls = get_non_english_links(wikipedia_urls)
    results = []
  
    for url in english_urls:
      print("CHECKING ", url)
      try:
          try:
              content = get_wikipedia_summary(url)
          except Exception as e:
              print(f"Error for getting wikipedia summary for {url}: {e}")
              record_error(f"Error for using wikipedia summary api for {url}: {e}", "errors.log")
              continue
          try:
              is_english_wikipedia_page = check_english_wikipedia_page(title, content)
          except Exception as e:
              print(f"Error for checking english wikipedia page for {url}: {e}")
              record_error(f"Error for checking wikipedia page with chatgpt for {url}: {e}", "errors.log")
              continue
          if is_english_wikipedia_page:
              print("yes")
              results.append(url)
              break
          else:
              print("no")
      except Exception as e:
          print(f"Error for checking particular url")
          
    
    # If the book is not english, look for non-english wikipedia results
    if language != "English":
      #print("LOOKING FOR NON-ENGLISH WIKIPEDIA")
      #print("CHECKING NON-ENGLISH URLS: ", non_english_urls)
      for url in non_english_urls:
          print("CHECKING ", url)
          try:
              try:
                  content = get_wikipedia_summary(url)
              except Exception as e:
                  print(f"Error for getting wikipedia summary for {url}: {e}")
                  record_error(f"Error for using wikipedia summary api for {url}: {e}", "errors.log")
                  continue
              try:
                  is_non_english_wikipedia_page = check_non_english_wikipedia_page(title, content, language)
              except Exception as e:
                  print(f"Error for checking non-english wikipedia page for {url}: {e}")
                  record_error(f"Error for checking wikipedia page with chatgpt for {url}: {e}", "errors.log")
                  continue
              if is_non_english_wikipedia_page:
                  print("yes")
                  results.append(url)
                  break
              else:
                  print("no")
          except Exception as e:
              print(f"Error for checking particular url")

    return results
  except Exception as e:
      print("Wikipedia link error for book id: ", book_id, " Error: ", e)
  time.sleep(5)
    


def save_book_wikis(book_id, urls):
    # convert your results into sql queries (but exclude legacy links)
    if urls: # Exclude books without urls
        urls = " ".join(urls)
        sql = f"insert into attributes (fk_books,fk_attriblist,text,nonfiling) values ({book_id},500,'{urls}',0);"
        print("SQL: ", sql)
        
        # save results
        with open('./results/wiki_for_books.txt', 'a') as f:
            f.write(f"{sql}\n")