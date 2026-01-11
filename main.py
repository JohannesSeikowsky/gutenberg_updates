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
    # @Rowan - IMPORTANT NOTE - The pipeline relies on the data as it's extracted in the code right below this comment. "title" for example is a scraping of the h1 tag of the page of the particular book, meaning it includes the book's title and also its author. "language" is obvious. "authors" and thus "author_str" also include translators, editors etc, but it's made obvious who the main author is! These details are very important for the various LLM layers within the pipeline to do their job well. The pipeline is tried and tested the exact way it is now. If you change the input data in any way, you'll need to carefully consider what adjustments will need to be made "downstream" to the pipeline itself.

    # Example 1: If you switch "title" to be the title from the db rather than the h1, Serper/Google will likely do a worse job since it isn't given the author. And if you give it author_str as a supplement, it may get confused because editors, translators etc are all included as well. (the h1 make a pretty good google search query).
    
    # Example 2: generate_wiki_based_summary() ensures that a wiki-based summary uses that h1 tag as the name of the work within the summary. If you don't do that, there is a good chance that for some summaries there will be a discrepancy between the title in the h1 and the title in the summary - which is just awkward. I've seen that.

    # These are just two examples on top of my head.

    # Overall - be careful with changing the input data to the pipeline. If you change it, odds are that the pipeline itself will also need to be adjusted. That may or may not be worthwhile (at any rate, if would definitely need to be tested well).

    book_content = get_book_content(book_id)
    title, language, authors = get_book_metadata(book_id)
    authors_str = "; ".join([a['name'] for a in authors if a['role'] == 'Author']) if authors else ""


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