import requests
from bs4 import BeautifulSoup
import re


def get_latest_book_id():
    """
    Fetch and return only the latest book ID from Project Gutenberg
    Returns:
        str: The latest book ID, or None if unable to fetch
    """
    base_url = "https://www.gutenberg.org"
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; GutenbergLatestBook/1.0; +https://github.com)'
    }

    try:
        # Fetch the homepage
        response = requests.get(
            base_url,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the latest book section
        latest_books = soup.find('div', class_='page_content').find_all('a')

        # Look for the first ebook link
        for link in latest_books:
            href = link.get('href', '')
            if '/ebooks/' in href:
                # Extract book ID
                book_id = re.search(r'/ebooks/(\d+)', href)
                if book_id:
                    return int(book_id.group(1))
        return None

    except requests.RequestException:
        return None


def get_book_content_by_id(book_id):
    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        book = cut_end(cut_beginning(response.text))
        return book, url
    except requests.RequestException as e:
        print(f"Error fetching book from website: {e}")
        return None


def fetch_title_and_author_from_website(book_id):
  url = f"https://www.gutenberg.org/ebooks/{book_id}"
  try:
      response = requests.get(url)
      soup = BeautifulSoup(response.content, 'html.parser')
      content_div = soup.find('div', id='content')
      title_tag = content_div.find('h1') if content_div else None
      title = title_tag.text.strip() if title_tag else "Title not found"
      return title
  except requests.RequestException as e:
      print(f"Error fetching book details: {e}")
      return None


def cut_beginning(text):    
  start_marker = "*** START OF"
  lines = text.split('\n')

  for i, line in enumerate(lines):
      if line.startswith(start_marker):
          return '\n'.join(lines[i+1:]).strip()
  return text


def cut_end(text):
  end_marker = "*** END OF"
  lines = text.split('\n')

  for i, line in enumerate(lines):
      if line.startswith(end_marker):
          return '\n'.join(lines[:i]).strip()
  return text