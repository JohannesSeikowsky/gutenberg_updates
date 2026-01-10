# Run complete pipeline for a test book to observe behavior at each step.

from utils import get_book_content, get_book_metadata
from summaries import summarise_book, format_summary
from wiki_based_summaries import generate_wiki_based_summary, exclude_short_articles, pick_longest_article
from categories import get_categories
from readability import calculate_readability_score
from wiki_for_books import get_book_wikipedia_links
from wiki_for_authors import get_author_metadata, get_author_wikipedia_link

test_case = 25500
# 35500 # no wikipedia article
# 25500 # one wikipedia article
# 2229 # Faust --> two wikipedia articles

print(f"=== Testing Pipeline for Book {test_case} ===\n")

# Fetch book data
print("Fetching book data from Gutenberg...")
book_content = get_book_content(test_case)
title, language, authors, _ = get_book_metadata(test_case)
authors_str = ", ".join([a['name'] for a in authors]) if authors else ""

print(f"  Title: {title}")
print(f"  Language: {language}")
print(f"  Authors: {authors_str}")
if book_content:
    print(f"  Book content: {len(book_content.split())} words")
else:
    print(f"  Book content: None")
print()

# 1. Book Wiki
print("--- Step 1: Finding Wikipedia links for book ---")
if title and language and authors_str:
    try:
        wiki_links = get_book_wikipedia_links(title, language, authors_str)
        if wiki_links:
            print(f"  ✓ Found {len(wiki_links)} Wikipedia link(s):")
            for link in wiki_links:
                print(f"    - {link}")
        else:
            print(f"  ✗ No Wikipedia links found")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        wiki_links = []
else:
    print(f"  ⊘ Skipped (missing title, language, or authors)")
    wiki_links = []
print()

# 2. Summary (Wikipedia-based first, then book content fallback)
print("--- Step 2: Generating summary ---")
if title:
    try:
        summary = None

        # Try Wikipedia-based summary
        if wiki_links:
            print("  Attempting Wikipedia-based summary...")
            try:
                valid_articles = exclude_short_articles(wiki_links)
                print(f"    - Articles after filtering out short ones: {len(valid_articles)}")

                article_text = pick_longest_article(valid_articles)
                if article_text:
                    word_count = len(article_text.split())
                    print(f"    - Selected longest article: {word_count} words")
                    print(f"    - Sending to Claude for summarization...")

                    summary = generate_wiki_based_summary(article_text, title)
                    if "insufficient information" in summary.lower():
                        print(f"    ✗ Claude determined insufficient information in Wikipedia article")
                        summary = None
                    else:
                        print(f"    ✓ Summary generated from Wikipedia")
                else:
                    print(f"    ✗ No valid article text after filtering")
            except Exception as e:
                print(f"    ✗ Wikipedia summary error: {e}")
                summary = None

        # Fall back to book content
        if not summary and book_content:
            print(f"  Falling back to book content summary...")
            print(f"    - Sending book content to GPT for summarization...")
            summary = summarise_book(book_content, title)
            print(f"    ✓ Summary generated from book content")

        if summary:
            summary = format_summary(summary)
            print(f"\n  Final Summary:\n  {summary}\n")
        else:
            print(f"  ✗ Could not generate summary")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        summary = None
else:
    print(f"  ⊘ Skipped (missing title)")
    summary = None
print()

# 3. Categories
print("--- Step 3: Assigning categories ---")
if summary:
    try:
        print(f"  Sending summary to GPT for categorization...")
        categories = get_categories(test_case, summary)
        print(f"  ✓ Categories assigned: {categories}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
else:
    print(f"  ⊘ Skipped (no summary available)")
print()

# 4. Readability
print("--- Step 4: Calculating readability score ---")
if book_content:
    try:
        print(f"  Calculating Flesch-Kincaid score...")
        readability = calculate_readability_score(book_content)
        print(f"  ✓ Readability score: {readability}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
else:
    print(f"  ⊘ Skipped (no book content)")
print()

# 5. Author Wiki
print("--- Step 5: Finding Wikipedia links for authors ---")
if authors:
    for author in authors:
        print(f"  Processing author: {author['name']}")
        try:
            author_metadata = get_author_metadata(author['id'])

            if author_metadata and not author_metadata.get('has_wiki_link', False):
                print(f"    - Searching for Wikipedia link via Perplexity...")
                wiki_link = get_author_wikipedia_link(author, author_metadata)
                if wiki_link:
                    print(f"    ✓ Found: {wiki_link}")
                else:
                    print(f"    ✗ No Wikipedia link found")
            else:
                print(f"    ⊘ Already has Wikipedia link in database")
        except Exception as e:
            print(f"    ✗ Error: {e}")
else:
    print(f"  ⊘ Skipped (no authors)")

print(f"\n=== Pipeline Test Complete ===")
