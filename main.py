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
from wiki_based_summaries import generate_wiki_based_summary, exclude_short_articles, pick_longest_article
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
    # Fetch all relevant data from Gutenberg once
    book_content = get_book_content(book_id)
    title, language, authors, _ = get_book_metadata(book_id)
    # It's important that it's clear in author_str who the main author is versus who the editors, translators etc. are. Else Claude will likely get confused when doing the "deep" validation.
    authors_str = ", ".join([a['name'] for a in authors]) if authors else ""

    # Print book header
    separator = "═" * 60
    title_display = title if title else "Unknown Title"
    language_display = language if language else "Unknown"
    authors_display = authors_str if authors_str else "Unknown"
    print(f"\n{separator}")
    print(f"Book #{book_id}: {title_display}")
    print(f"Language: {language_display} | Authors: {authors_display}")
    print(f"{separator}\n")


    # Find Wikipedia link(s) for book
    if title and language and authors_str:
        try:
            wiki_links = get_book_wikipedia_links(title, language, authors_str)
            count = len(wiki_links)
            result = f"{count} validated" if count > 0 else "No match found"
            print(f"[Step 1/5] Book Wikipedia: {result}")
            save_book_wikis_sql(book_id, wiki_links, results_file)
        except Exception as e:
            print("[Step 1/5] Book Wikipedia: Error")
            log_error(f"{book_id}, Book wiki, {e}", errors_file)
            wiki_links = []
    else:
        print("[Step 1/5] Book Wikipedia: Skipped (missing data)")
        wiki_links = []
    time.sleep(STEP_DELAY)


    # Generate summary
    # Try to summarise using a Wikipedia article, if not possible fall back to book content method.
    if title:
        try:
            summary = None
            # New approach: summarise using a Wikipedia article
            if wiki_links:
                try:
                    print("  Generating summary from Wikipedia...")
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
                print(f"[Step 2/5] Summary: Generated from Wikipedia")

            # Existing approach: summarise using book content
            if not summary and book_content:
                summary = summarise_book(book_content, title)
                print(f"[Step 2/5] Summary: Generated from book content")

            if summary:
                summary = format_summary(summary)
                save_summary_sql(book_id, summary, results_file)
            else:
                print("[Step 2/5] Summary: Could not generate")
        except Exception as e:
            print("[Step 2/5] Summary: Error")
            log_error(f"{book_id}, Summary, {e}", errors_file)
            summary = None
    else:
        print("[Step 2/5] Summary: Skipped (missing data)")
        summary = None
    time.sleep(STEP_DELAY)


    # Generate categories
    if summary:
        try:
            print("  Assigning categories...")
            categories = get_categories(book_id, summary)
            categories_str = ", ".join(categories)
            print(f"[Step 3/5] Categories: {categories_str}")
            save_categories_sql(book_id, categories, results_file)
        except Exception as e:
            print("[Step 3/5] Categories: Error")
            log_error(f"{book_id}, Categories, {e}", errors_file)
    else:
        print("[Step 3/5] Categories: Skipped (missing summary)")
    time.sleep(STEP_DELAY)


    # Calculate readability score
    if book_content:
        try:
            print("  Calculating readability...")
            readability = calculate_readability_score(book_content)
            print(f"[Step 4/5] Readability: {readability}")
            save_readability_sql(book_id, readability, results_file)
        except Exception as e:
            print("[Step 4/5] Readability: Error")
            log_error(f"{book_id}, Readability, {e}", errors_file)
    else:
        print("[Step 4/5] Readability: Skipped (missing data)")
    time.sleep(STEP_DELAY)


    # Find Wikipedia links for authors
    if authors:
        for author in authors:
            try:
                author_id = author['id']
                author_metadata = get_author_metadata(author_id)

                if author_metadata and not author_metadata.get('has_wiki_link', False):
                    wiki_link = get_author_wikipedia_link(author, author_metadata)
                    if wiki_link:
                        save_author_wiki_sql(author_id, wiki_link, results_file)
                        print(f"[Step 5/5] Author Wikipedia: {wiki_link}")
                    else:
                        print("[Step 5/5] Author Wikipedia: Not found")
                else:
                    print("[Step 5/5] Author Wikipedia: Already has link")
            except Exception as e:
                log_error(f"{book_id}, Author wiki {author_id}, {e}", errors_file)
    else:
        print("[Step 5/5] Author Wikipedia: Skipped (no authors)")
    time.sleep(STEP_DELAY)

    save_last_processed_id(book_id)