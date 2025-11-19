import requests
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

load_dotenv()


def get_latest_book_id():
    """Fetch and return the latest book ID from Project Gutenberg (so we know when to stop processing new books)."""
    try:
        response = requests.get(
            "https://www.gutenberg.org",
            headers={'User-Agent': 'Mozilla/5.0 (compatible; GutenbergLatestBook/1.0; +https://github.com)'},
            timeout=10
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find('div', class_='page_content').find_all('a'):
            if match := re.search(r'/ebooks/(\d+)', link.get('href', '')):
                return int(match.group(1))
        return None
    except requests.RequestException:
        return None


def get_book_content(book_id):
    """Fetches the content of a book from Project Gutenberg and cuts the Gutenberg header and footer."""
    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; GutenbergContent/1.0; +https://github.com)'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        book = cut_end(cut_beginning(response.text))
        return book
    except requests.RequestException as e:
        print(f"Error fetching book from website: {e}")
        return None


def get_book_metadata(book_id):
    """
    Fetch all book metadata from Project Gutenberg in one request.
    Returns tuple: (title, language, authors, has_wiki_link)
    Always returns a tuple with defaults if data is unavailable.
    """
    url = f"https://www.gutenberg.org/ebooks/{book_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; GutenbergMetadata/1.0; +https://github.com)'
    }

    # Default values
    result = {
        'title': None,
        'language': None,
        'authors': [],
        'has_wiki_link': False
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title
        content_div = soup.find('div', id='content')
        title_tag = content_div.find('h1') if content_div else None
        if title_tag:
            result['title'] = title_tag.text.strip()

        # Extract language
        bibrec_table = soup.find('table', class_='bibrec')
        if bibrec_table:
            for row in bibrec_table.find_all('tr'):
                header = row.find('th')
                if header and 'Language' in header.text:
                    data = row.find('td')
                    if data:
                        result['language'] = data.text.strip()
                        break

        # Extract authors (with IDs, names, life dates, roles)
        if bibrec_table:
            for row in bibrec_table.find_all('tr'):
                header = row.find('th')
                if header:
                    role = header.text.strip()
                    if role in ['Author', 'Editor', 'Translator', 'Contributor', 'Illustrator']:
                        data = row.find('td')
                        if data:
                            link = data.find('a', href=True)
                            if link and '/ebooks/author/' in link['href']:
                                author_id = link['href'].split('/')[-1]
                                full_name = link.text.strip()

                                # Extract life dates from name (format: "Name, dates" or "Name (full), dates")
                                life_dates = ''
                                name = full_name

                                # Look for date patterns like "1857-1920" or "-1912" or "1857-"
                                date_match = re.search(r',\s*(\d{4}?-\d{4}?|\d{4}-|-\d{4})$', full_name)
                                if date_match:
                                    life_dates = date_match.group(1)
                                    name = full_name[:date_match.start()].strip()

                                result['authors'].append({
                                    'id': author_id,
                                    'name': name,
                                    'life_dates': life_dates,
                                    'role': role
                                })

        # Check if book already has Wikipedia link
        if bibrec_table:
            for row in bibrec_table.find_all('tr'):
                if 'wikipedia.org' in str(row):
                    result['has_wiki_link'] = True
                    break

    except requests.RequestException as e:
        print(f"Error fetching book metadata: {e}")

    return result['title'], result['language'], result['authors'], result['has_wiki_link']


def cut_beginning(text):
  """Cut the beginning of the book to remove the Gutenberg header."""
  start_marker = "*** START OF"
  lines = text.split('\n')

  for i, line in enumerate(lines):
      if line.startswith(start_marker):
          return '\n'.join(lines[i+1:]).strip()
  return text


def cut_end(text):
  """Cut the end of the book to remove the Gutenberg footer (legal stuff)."""
  end_marker = "*** END OF"
  lines = text.split('\n')

  for i, line in enumerate(lines):
      if line.startswith(end_marker):
          return '\n'.join(lines[:i]).strip()
  return text


def record_error(error, file):
    with open(file, "a") as f:
        f.write(error + "\n")


def record_latest_completed_id(book_id):
    with open("latest_id.txt", "w") as f:
        f.write(str(book_id))


def get_latest_completed_id():
    return int(open("latest_id.txt", "r").read())