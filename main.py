# Update New Releases on Gutenberg
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

for book_id in range(from_id+1, to_id+1):
  print("Book: ", book_id)
  now = datetime.now()
  current_month = now.strftime("%m")
  current_year = now.strftime("%y")
  results_file = f"results/update_{current_month}_{current_year}.txt"
  errors_file = f"errors/errors_{current_month}_{current_year}.txt"

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
  
  # record id of the latest book that has been processed
  record_latest_completed_id(book_id)
  print("---------------------  ")




# # Email results to me
# recipient = "joseikowsky@gmail.com"
# subject_line = f"Gutenberg Updates for {current_month}.{current_year}"
# content = ""
# file_content = open(results_file, "r").read()
# file_name = f"updates_{current_month}_{current_year}.txt"
# email_with_attachment(recipient, subject_line, content, file_content, file_name)
# time.sleep(6)

# # Email errors to me
# subject_line = f"Errors"
# content = ""  
# if os.path.exists(errors_file):
#   file_content = open(errors_file, "r").read()
# else:
#   subject_line = "No Errors found."
#   file_content = ""
# file_name = f"errors_{current_month}_{current_year}.txt"
# email_with_attachment(recipient, subject_line, content, file_content, file_name)



# run code once a month on 28th -- cal entry
# download & run code locally // o repl?


# with open("check_category_results.txt", "w") as f:
#   test_set = open("categories_test.txt").read().split("\n")
#   for query in test_set:
#     try:
#       book_id = query.split("values (")[1].split(",520")[0]
#       summary = query.split("520,'")[1].split(" (This is an automatically")[0]   
#       category_choice = get_categories(book_id, summary)
#       category_ids = save_categories(book_id, category_choice)
#       print(book_id)
#       print(summary)
#       print(category_choice)
#       print(category_ids)
#       print("---")
#       f.write(f"{book_id}\n{summary}\n{category_choice}\n{category_ids}\n---\n")
#     except Exception as e:
#       print(e)