# Main Script
# Goes over all new book release on Gutenberg and for each generates:
# - Summary
# - Wikipedia links for the book
# - Readability score
# - Categories
# - Wikipedia links for the authors

# Results get saved in the results/ directory in a file named after the current month.

from summaries import summarise_book, save_summary
from readability import calculate_readability, save_readability
from wiki_for_books import get_book_wikipedia_links, save_book_wikis, book_has_wiki
from wiki_for_authors import get_author_wikipedia_links
from categories import get_categories, save_categories
from utils import *
from datetime import datetime
import time
import os

from_id = get_latest_completed_id()
to_id = get_latest_book_id()
print("From: ", from_id, "To: ", to_id)
print("---")

now = datetime.now()
results_file = f"results/update_{now.strftime('%m_%y')}.txt"
errors_file = f"errors/errors_{now.strftime('%m_%y')}.txt"

for book_id in range(from_id+1, to_id+1):
  print("Book: ", book_id)

  try:
    summary = summarise_book(book_id)
    print(summary + "\n\n")
    save_summary(book_id, summary, results_file)
  except Exception as e:
    print("Summary Error\n\n")
    record_error(f"{book_id}, Summary Error, {e}", errors_file)
  time.sleep(1)

  try:
    if not book_has_wiki(book_id):
      wiki_links = get_book_wikipedia_links(book_id)
      print("Wikis for Book:", wiki_links, "\n\n")
      save_book_wikis(book_id, wiki_links, results_file)
    else:
      print("Wiki for Book already on Gutenberg.\n\n")
  except Exception as e:
    print("Wiki for Books Error\n\n")
    record_error(f"{book_id}, Wiki for Books Error, {e}", errors_file)
  time.sleep(1)

  try:
    readability = calculate_readability(book_id)
    print("Readability:", readability, "\n\n")
    save_readability(book_id, readability, results_file)
  except Exception as e:
    print("Readability Error\n\n")
    record_error(f"{book_id}, Readability Error, {e}", errors_file)
  time.sleep(1)

  try:
    categories = get_categories(book_id, summary)
    print("Categories: ", categories, "\n\n")
    save_categories(book_id, categories, results_file)
  except Exception as e:
    print("Categories Error\n\n")
    record_error(f"{book_id}, Categories Error, {e}", errors_file)
  time.sleep(1)

  try:
    get_author_wikipedia_links(book_id, results_file) # saving in function itself.
  except Exception as e:
    print("Wiki for Authors Error\n\n")
    record_error(f"{book_id}, Wiki for Authors Error, {e}", errors_file)
  time.sleep(3)
  
  record_latest_completed_id(book_id)
  print("---------------------  ")