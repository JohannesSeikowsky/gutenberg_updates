# Run complete pipeline for a test book to observe behavior at each step.

from utils import get_book_content, get_book_metadata
from summaries import summarise_book, format_summary
from wiki_based_summaries import generate_wiki_based_summary, exclude_short_articles, pick_longest_article
from categories import get_categories
from readability import calculate_readability_score
from wiki_for_books import get_book_wikipedia_links
from wiki_for_authors import get_author_metadata, get_author_wikipedia_link

# Open test_results.txt for writing (overrides previous content)
output_file = open('test_results.txt', 'w')

def log(message=''):
    """Print to console and write to test_results.txt."""
    print(message)
    output_file.write(message + '\n')

test_case = 25500
# 35500 # no wikipedia article
# 25500 # one wikipedia article
# 2229 # Faust --> two wikipedia articles

log(f"=== Testing Pipeline for Book {test_case} ===\n")

# Fetch book data
log("Fetching book data from Gutenberg...")
book_content = get_book_content(test_case)
title, language, authors, _ = get_book_metadata(test_case)
authors_str = ", ".join([a['name'] for a in authors]) if authors else ""

log(f"  Title: {title}")
log(f"  Language: {language}")
log(f"  Authors: {authors_str}")
if book_content:
    log(f"  Book content: {len(book_content.split())} words")
else:
    log(f"  Book content: None")
log()

# 1. Book Wiki
log("--- Step 1: Finding Wikipedia links for book ---")
if title and language and authors_str:
    try:
        wiki_links = get_book_wikipedia_links(title, language, authors_str)
        if wiki_links:
            log(f"  ✓ Found {len(wiki_links)} Wikipedia link(s):")
            for link in wiki_links:
                log(f"    - {link}")
        else:
            log(f"  ✗ No Wikipedia links found")
    except Exception as e:
        log(f"  ✗ Error: {e}")
        wiki_links = []
else:
    log(f"  ⊘ Skipped (missing title, language, or authors)")
    wiki_links = []
log()

# 2. Summary (Wikipedia-based first, then book content fallback)
log("--- Step 2: Generating summary ---")
if title:
    try:
        summary = None

        # Try Wikipedia-based summary
        if wiki_links:
            log("  Attempting Wikipedia-based summary...")
            try:
                valid_articles = exclude_short_articles(wiki_links)
                log(f"    - Articles after filtering out short ones: {len(valid_articles)}")

                article_text = pick_longest_article(valid_articles)
                if article_text:
                    word_count = len(article_text.split())
                    log(f"    - Selected longest article: {word_count} words")
                    log(f"    - Sending to Claude for summarization...")

                    summary = generate_wiki_based_summary(article_text, title)
                    if "insufficient information" in summary.lower():
                        log(f"    ✗ Claude determined insufficient information in Wikipedia article")
                        summary = None
                    else:
                        log(f"    ✓ Summary generated from Wikipedia")
                else:
                    log(f"    ✗ No valid article text after filtering")
            except Exception as e:
                log(f"    ✗ Wikipedia summary error: {e}")
                summary = None

        # Fall back to book content
        if not summary and book_content:
            log(f"  Falling back to book content summary...")
            log(f"    - Sending book content to GPT for summarization...")
            summary = summarise_book(book_content, title)
            log(f"    ✓ Summary generated from book content")

        if summary:
            summary = format_summary(summary)
            log(f"\n  Final Summary:\n  {summary}\n")
        else:
            log(f"  ✗ Could not generate summary")
    except Exception as e:
        log(f"  ✗ Error: {e}")
        summary = None
else:
    log(f"  ⊘ Skipped (missing title)")
    summary = None
log()

# 3. Categories
log("--- Step 3: Assigning categories ---")
if summary:
    try:
        log(f"  Sending summary to GPT for categorization...")
        categories = get_categories(test_case, summary)
        log(f"  ✓ Categories assigned: {categories}")
    except Exception as e:
        log(f"  ✗ Error: {e}")
else:
    log(f"  ⊘ Skipped (no summary available)")
log()

# 4. Readability
log("--- Step 4: Calculating readability score ---")
if book_content:
    try:
        log(f"  Calculating Flesch-Kincaid score...")
        readability = calculate_readability_score(book_content)
        log(f"  ✓ Readability score: {readability}")
    except Exception as e:
        log(f"  ✗ Error: {e}")
else:
    log(f"  ⊘ Skipped (no book content)")
log()

# 5. Author Wiki
log("--- Step 5: Finding Wikipedia links for authors ---")
if authors:
    for author in authors:
        log(f"  Processing author: {author['name']}")
        try:
            author_metadata = get_author_metadata(author['id'])

            if author_metadata and not author_metadata.get('has_wiki_link', False):
                log(f"    - Searching for Wikipedia link via Perplexity...")
                wiki_link = get_author_wikipedia_link(author, author_metadata)
                if wiki_link:
                    log(f"    ✓ Found: {wiki_link}")
                else:
                    log(f"    ✗ No Wikipedia link found")
            else:
                log(f"    ⊘ Already has Wikipedia link in database")
        except Exception as e:
            log(f"    ✗ Error: {e}")
else:
    log(f"  ⊘ Skipped (no authors)")

log(f"\n=== Pipeline Test Complete ===")

# Close output file
output_file.close()
