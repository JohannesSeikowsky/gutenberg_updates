# Hyper-minimalistic test. Run to see whether the core functionalities work as expected after changes.
# The test case is "La Divina Commedia di Dante" because has wikipedia links for both the book and the author.


from utils import get_book_content, get_book_metadata
from summaries import summarise_book
from categories import get_categories
from readability import calculate_readability
from wiki_for_books import get_book_wikipedia_links
from wiki_for_authors import (
    get_author_metadata,
    exclude_already_done_authors,
    get_author_wikipedia_link
)

test_case = 1000
book_content = get_book_content(test_case)
title, language, authors, has_wiki_link = get_book_metadata(test_case)
print(title, language, authors, has_wiki_link, sep="\n")

summary = summarise_book(book_content, title)
print(f"Summary: {summary}")

categories = get_categories(test_case, summary)
print(f"Categories: {categories}")

readability = calculate_readability(book_content)
print(f"Readability: {readability}")

wiki_links = get_book_wikipedia_links(title, language)
print(f"Book Wikipedia: {wiki_links}")

for author in authors:
    author_metadata = get_author_metadata( author['id']) # finds other books by the author
    wiki_link = get_author_wikipedia_link(author, author_metadata)
    print(f"Author Wikipedia: {wiki_link}")
