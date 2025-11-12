# Main Script
# Goes over all new book releases on Gutenberg since the last update was run and for each generates:
# - Summary
# - Wikipedia links for the book
# - Readability score
# - Categories
# - Wikipedia links for the authors
# Results get saved in "results/", Errors in "errors/". Both in a file named after the current month.
# Results are saved as SQL INSERT statements (as requested by Greg).

import time
from datetime import datetime
from utils import *
from summaries import summarise_book, save_summary
from readability import calculate_readability, save_readability
from wiki_for_books import get_book_wikipedia_links, save_book_wikis, book_has_wiki
from wiki_for_authors import get_author_wikipedia_links
from categories import get_categories, save_categories

STEP_DELAY = 1

start_id = get_latest_completed_id()
end_id = get_latest_book_id()
print(f"Processing books {start_id + 1} to {end_id}")
print("---")

month_year = datetime.now().strftime('%m_%y')
results_file = f"results/update_{month_year}.txt"
errors_file = f"errors/errors_{month_year}.txt"

for book_id in range(start_id + 1, end_id + 1):
    print(f"Book: {book_id}")

    # Generate summary
    try:
        summary = summarise_book(book_id)
        print(f"Summary: {summary}")
        save_summary(book_id, summary, results_file)
    except Exception as e:
        print("Summary: Error")
        record_error(f"{book_id}, Summary, {e}", errors_file)
    time.sleep(STEP_DELAY)

    # Find Wikipedia links for book
    try:
        if not book_has_wiki(book_id):
            wiki_links = get_book_wikipedia_links(book_id)
            print(f"Book wiki: {wiki_links}")
            save_book_wikis(book_id, wiki_links, results_file)
        else:
            print("Book wiki: Already exists")
    except Exception as e:
        print("Book wiki: Error")
        record_error(f"{book_id}, Book wiki, {e}", errors_file)
    time.sleep(STEP_DELAY)

    # Calculate readability score
    try:
        readability = calculate_readability(book_id)
        print(f"Readability: {readability}")
        save_readability(book_id, readability, results_file)
    except Exception as e:
        print("Readability: Error")
        record_error(f"{book_id}, Readability, {e}", errors_file)
    time.sleep(STEP_DELAY)

    # Generate categories
    try:
        categories = get_categories(book_id, summary)
        print(f"Categories: {categories}")
        save_categories(book_id, categories, results_file)
    except Exception as e:
        print("Categories: Error")
        record_error(f"{book_id}, Categories, {e}", errors_file)
    time.sleep(STEP_DELAY)

    # Find Wikipedia links for authors
    try:
        get_author_wikipedia_links(book_id, results_file)
    except Exception as e:
        print("Author wiki: Error")
        record_error(f"{book_id}, Author wiki, {e}", errors_file)
    time.sleep(STEP_DELAY)

    record_latest_completed_id(book_id)
    print("---------------------")