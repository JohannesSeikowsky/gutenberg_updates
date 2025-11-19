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
from wiki_for_books import get_book_wikipedia_links, save_book_wikis
from wiki_for_authors import (
    get_author_metadata,
    exclude_already_done_authors,
    record_author_as_done,
    get_author_wikipedia_link,
    save_author_wikipedia_link
)
from categories import get_categories, save_categories

STEP_DELAY = 1

start_id = get_latest_completed_id()
end_id = get_latest_book_id()
print(f"Processing books {start_id + 1} to {end_id}")

month_year = datetime.now().strftime('%m_%y')
results_file = f"results/update_{month_year}.txt"
errors_file = f"errors/errors_{month_year}.txt"

for book_id in range(start_id + 1, end_id + 1):
    print(f"Book: {book_id}")

    # Fetch all relevant data for book from Gutenberg once
    book_content = get_book_content(book_id)
    title, language, authors, has_wiki_link = get_book_metadata(book_id)
    print(title, language, authors, has_wiki_link, sep="\n")

    # Generate summary
    if book_content and title:
        try:
            summary = summarise_book(book_content, title)
            print(f"Summary: {summary}")
            save_summary(book_id, summary, results_file)
        except Exception as e:
            print("Summary: Error")
            record_error(f"{book_id}, Summary, {e}", errors_file)
    else:
        print("Summary: Skipped (missing data)")
        summary = None
    time.sleep(STEP_DELAY)

    # Find Wikipedia links for book
    if title and language:
        try:
            if not has_wiki_link:
                wiki_links = get_book_wikipedia_links(title, language)
                print(f"Book wiki: {wiki_links}")
                save_book_wikis(book_id, wiki_links, results_file)
            else:
                print("Book wiki: Already exists")
        except Exception as e:
            print("Book wiki: Error")
            record_error(f"{book_id}, Book wiki, {e}", errors_file)
    else:
        print("Book wiki: Skipped (missing data)")
    time.sleep(STEP_DELAY)

    # Calculate readability score
    if book_content:
        try:
            readability = calculate_readability(book_content)
            print(f"Readability: {readability}")
            save_readability(book_id, readability, results_file)
        except Exception as e:
            print("Readability: Error")
            record_error(f"{book_id}, Readability, {e}", errors_file)
    else:
        print("Readability: Skipped (missing data)")
    time.sleep(STEP_DELAY)

    # Generate categories
    if summary:
        try:
            categories = get_categories(book_id, summary)
            print(f"Categories: {categories}")
            save_categories(book_id, categories, results_file)
        except Exception as e:
            print("Categories: Error")
            record_error(f"{book_id}, Categories, {e}", errors_file)
    else:
        print("Categories: Skipped (missing summary)")
    time.sleep(STEP_DELAY)

    # Find Wikipedia links for authors
    if authors:
        authors = exclude_already_done_authors(authors)
        for author in authors:
            try:
                author_id = author['id']
                author_metadata = get_author_metadata(author_id)

                if author_metadata and not author_metadata['has_wiki_link']:
                    wiki_link = get_author_wikipedia_link(author, author_metadata)
                    if wiki_link:
                        save_author_wikipedia_link(author_id, wiki_link, results_file)
                        print(f"Author wiki: {wiki_link}")
                    else:
                        print("Author wiki: Not found")
                else:
                    print("Author wiki: Already exists")

                record_author_as_done(author_id)
            except Exception as e:
                record_error(f"{book_id}, Author wiki {author_id}, {e}", errors_file)
                record_author_as_done(author_id)
    else:
        print("Author wiki: Skipped (no authors)")
    time.sleep(STEP_DELAY)

    record_latest_completed_id(book_id)
    print("---------------------")




# Readme
# done_authors.txt necessary?

# important commments?
# more simplification
# data getting --> to be done in pipeline anyway