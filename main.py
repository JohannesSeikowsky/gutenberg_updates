# Main Script
# Goes over all new book releases on Gutenberg since the last update was run and for each generates:
# - Wikipedia links for the book
# - Summary - either based on the book's wikipedia article if there is one, or based on the book itself
# - Readability score
# - Categories
# - Wikipedia links for the authors
# Results get saved in "results/", Errors in "errors/". Both in a file named after the current month.
# Results are saved as SQL INSERT statements (as requested by Greg).

import time
from datetime import datetime
from utils import *
from summaries import (
    summarise_book,
    save_summary_sql,
    format_summary
)
from wiki_based_summaries import download_wikipedia_article, generate_wiki_based_summary, exclude_short_articles, pick_longest_article
from readability import calculate_readability_score, save_readability_sql
from wiki_for_books import get_book_wikipedia_links, save_book_wikis_sql
from wiki_for_authors import (
    get_author_metadata,
    get_author_wikipedia_link,
    save_author_wiki_sql
)
from categories import get_categories, save_categories_sql

STEP_DELAY = 1

start_id = load_last_processed_id()
end_id = get_latest_book_id()
print(f"Processing books {start_id + 1} to {end_id}")

month_year = datetime.now().strftime('%m_%y')
results_file = f"results/update_{month_year}.txt"
errors_file = f"errors/errors_{month_year}.txt"

for book_id in range(start_id + 1, end_id + 1):
    print(f"Book: {book_id}")

    # Fetch all relevant data from Gutenberg once
    book_content = get_book_content(book_id)
    title, language, authors, has_wiki_link = get_book_metadata(book_id)
    authors_str = ", ".join([a['name'] for a in authors]) # It's important that it's clear in this string who the main author is versus who the editors, translators etc. are. Else Claude will likely get confused when doing the "deep" valdation the validating.
    print(title, language, authors, has_wiki_link, sep="\n")

    # Find Wikipedia links for book and validate them
    if title and language:
        try:
            wiki_links = get_book_wikipedia_links(title, language, authors_str)
            print(f"Book wiki: {wiki_links}")
            save_book_wikis_sql(book_id, wiki_links, results_file)
        except Exception as e:
            print("Book wiki: Error")
            log_error(f"{book_id}, Book wiki, {e}", errors_file)
            wiki_links = []
    else:
        print("Book wiki: Skipped (missing data)")
        wiki_links = []
    time.sleep(STEP_DELAY)

    # Generate summary
    # Try to do based on a Wikipedia article, if not possible fall back to book content method.
    if book_content and title:
        try:
            summary = None
            # New approach: summary based on Wikipedia article
            if wiki_links:
                try:
                    valid_articles = exclude_short_articles(wiki_links)
                    article_text = pick_longest_article(valid_articles)

                    if article_text:
                        summary = generate_wiki_based_summary(article_text, title)
                        # Claude may decide that there's not enough information for a summary.
                        if "insufficient information" in summary.lower():
                            summary = None
                except Exception:
                    summary = None

            if summary:
                print(f"Summary: Generated from Wikipedia")

            # Existing approach: summary from book content
            if not summary:
                summary = summarise_book(book_content, title)
                print(f"Summary: Generated from book content")

            summary = format_summary(summary)
            save_summary_sql(book_id, summary, results_file)
        except Exception as e:
            print("Summary: Error")
            log_error(f"{book_id}, Summary, {e}", errors_file)
            summary = None
    else:
        print("Summary: Skipped (missing data)")
        summary = None
    time.sleep(STEP_DELAY)

    # Generate categories
    if summary:
        try:
            categories = get_categories(book_id, summary)
            print(f"Categories: {categories}")
            save_categories_sql(book_id, categories, results_file)
        except Exception as e:
            print("Categories: Error")
            log_error(f"{book_id}, Categories, {e}", errors_file)
    else:
        print("Categories: Skipped (missing summary)")
    time.sleep(STEP_DELAY)

    # Calculate readability score
    if book_content:
        try:
            readability = calculate_readability_score(book_content)
            print(f"Readability: {readability}")
            save_readability_sql(book_id, readability, results_file)
        except Exception as e:
            print("Readability: Error")
            log_error(f"{book_id}, Readability, {e}", errors_file)
    else:
        print("Readability: Skipped (missing data)")
    time.sleep(STEP_DELAY)

    # Find Wikipedia links for authors
    if authors:
        for author in authors:
            try:
                author_id = author['id']
                author_metadata = get_author_metadata(author_id)

                if author_metadata and not author_metadata['has_wiki_link']:
                    wiki_link = get_author_wikipedia_link(author, author_metadata)
                    if wiki_link:
                        save_author_wiki_sql(author_id, wiki_link, results_file)
                        print(f"Author wiki: {wiki_link}")
                    else:
                        print("Author wiki: Not found")
                else:
                    print("Author already has a Wikipedia link")
            except Exception as e:
                log_error(f"{book_id}, Author wiki {author_id}, {e}", errors_file)
    else:
        print("Author wiki: Skipped (no authors)")
    time.sleep(STEP_DELAY)

    save_last_processed_id(book_id)
    print("---------------------")