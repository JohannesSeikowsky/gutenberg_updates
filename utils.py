import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import unquote
from dotenv import load_dotenv

load_dotenv()


# Text processing helpers
def remove_gutenberg_wrapper(text):
    """Remove Gutenberg header and footer from book text."""
    lines = text.split('\n')
    start_index = 0
    end_index = len(lines)

    for i, line in enumerate(lines):
        if line.startswith("*** START OF"):
            start_index = i + 1
        elif line.startswith("*** END OF"):
            end_index = i
            break

    return '\n'.join(lines[start_index:end_index]).strip()


# Gutenberg functions
def get_latest_book_id():
    """Return the latest book ID from Project Gutenberg homepage."""
    try:
        response = requests.get(
            "https://www.gutenberg.org",
            headers={'User-Agent': 'Mozilla/5.0 (compatible; GutenbergLatestBook/1.0; +https://github.com)'},
            timeout=10
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        page_content = soup.find('div', class_='page_content')

        if not page_content:
            return None

        for link in page_content.find_all('a'):
            if match := re.search(r'/ebooks/(\d+)', link.get('href', '')):
                return int(match.group(1))
        return None
    except requests.RequestException:
        return None


def get_book_content(book_id):
    """Return book text with Gutenberg header and footer removed."""
    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    try:
        response = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; GutenbergContent/1.0; +https://github.com)'},
            timeout=10
        )
        response.raise_for_status()
        return remove_gutenberg_wrapper(response.text)
    except requests.RequestException as e:
        print(f"Error fetching book from website: {e}")
        return None


def get_book_metadata(book_id):
    """Return tuple: (title, language, authors, has_wiki_link) for the given book."""
    url = f"https://www.gutenberg.org/ebooks/{book_id}"
    metadata = {'title': None, 'language': None, 'authors': [], 'has_wiki_link': False}

    try:
        response = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; GutenbergMetadata/1.0; +https://github.com)'},
            timeout=10
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title
        content_div = soup.find('div', id='content')
        if content_div and (title_tag := content_div.find('h1')):
            metadata['title'] = title_tag.text.strip()

        bibrec_table = soup.find('table', class_='bibrec')
        if not bibrec_table:
            return metadata['title'], metadata['language'], metadata['authors'], metadata['has_wiki_link']

        # Extract language, authors, and check for Wikipedia link
        author_roles = ['Author', 'Editor', 'Translator', 'Contributor', 'Illustrator']
        for row in bibrec_table.find_all('tr'):
            header_cell = row.find('th')
            if not header_cell:
                continue

            role = header_cell.text.strip()

            # Extract language
            if 'Language' in role:
                if value_cell := row.find('td'):
                    metadata['language'] = value_cell.text.strip()

            # Extract authors
            elif role in author_roles:
                value_cell = row.find('td')
                if value_cell and (author_link := value_cell.find('a', href=True)) and '/ebooks/author/' in author_link['href']:
                    author_id = author_link['href'].split('/')[-1]
                    full_name = author_link.text.strip()
                    name = full_name
                    life_dates = ''

                    # Extract life dates from name (format: "Name, dates")
                    if date_match := re.search(r',\s*(\d{4}?-\d{4}?|\d{4}-|-\d{4})$', full_name):
                        life_dates = date_match.group(1)
                        name = full_name[:date_match.start()].strip()

                    metadata['authors'].append({
                        'id': author_id,
                        'name': name,
                        'life_dates': life_dates,
                        'role': role
                    })

            # Check for Wikipedia link
            if 'wikipedia.org' in str(row):
                metadata['has_wiki_link'] = True

    except requests.RequestException as error:
        print(f"Error fetching book metadata: {error}")

    return metadata['title'], metadata['language'], metadata['authors'], metadata['has_wiki_link']


# State management functions
def load_last_processed_id():
    """Read and return the last processed book ID from latest_id.txt."""
    with open("latest_id.txt", "r") as f:
        return int(f.read())


def save_last_processed_id(book_id):
    """Save the latest successfully processed book ID to latest_id.txt."""
    with open("latest_id.txt", "w") as f:
        f.write(str(book_id))


def log_error(error_message, log_file):
    """Append error message to the specified log file."""
    with open(log_file, "a") as f:
        f.write(f"{error_message}\n")


# Wikipedia functions
def download_wikipedia_article(url):
    """Download Wikipedia article content from URL."""
    # Extract language code from URL
    lang_match = re.search(r'https?://([a-z]{2,3})\.wikipedia\.org', url)
    if not lang_match:
        raise ValueError(f"Could not extract language code from URL: {url}")
    lang = lang_match.group(1)

    # Extract page title from URL
    title_match = re.search(r'/wiki/(.+)$', url.strip())
    if not title_match:
        raise ValueError(f"Could not extract page title from URL: {url}")
    page_title = unquote(title_match.group(1))

    # Call Wikipedia API
    api_url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'extracts',
        'explaintext': True,
        'redirects': 1,
        'titles': page_title
    }
    headers = {'User-Agent': 'WikiBookScraper/1.0 (Educational project)'}

    response = requests.get(api_url, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    pages = data.get('query', {}).get('pages', {})

    if not pages:
        raise ValueError("Empty API response")

    page = next(iter(pages.values()))

    if 'missing' in page:
        raise ValueError("Page does not exist")

    content = page.get('extract', '')
    if not content:
        raise ValueError("Empty article content")

    return content