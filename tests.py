# Run pipeline functions individually or all together for a specifc test book.
# "La Divina Commedia di Dante" is the test book, since it has both a book and author wikipedia link.

from utils import get_book_content, get_book_metadata
from summaries import summarise_book
from categories import get_categories
from readability import calculate_readability_score
from wiki_for_books import get_book_wikipedia_links
from validate_book_wiki import validate_wiki_link
from wiki_for_authors import (
    get_author_metadata,
    get_author_wikipedia_link
)

test_case = 8438

# Interactive function selection
print("Select functions to run (e.g., '1,2,4' or '6' for all):")
print("1: Summary | 2: Categories | 3: Readability | 4: Book Wiki | 5: Author Wiki | 6: All")
choice = input("> ").strip()

selected = choice.split(',')
run_all = '6' in selected

# Fetch data once
book_content = get_book_content(test_case)
title, language, authors, has_wiki_link = get_book_metadata(test_case)
print(title, language, authors, has_wiki_link, sep="\n")

# Run selected functions
if '1' in selected or run_all:
    summary = summarise_book(book_content, title)
    print(f"Summary: {summary}")
else:
    summary = None

if '2' in selected or run_all:
    if not summary:
        summary = """
        "La Divina Commedia di Dante: Complete" by Dante Alighieri is an epic poem written in the 14th century.
        The work explores themes of morality, spirituality, and the afterlife as it follows the journey of the
        protagonist, Dante, through the realms of Hell, Purgatory, and Heaven, guided initially by the Roman poet
        Virgil. At the start of the narrative, Dante finds himself lost in a dark forest, representing sin and
        confusion, realizing he has strayed from the righteous path. Struggling with despair, he encounters various
        allegorical beasts that symbolize different sins and obstacles in life. After invoking the muses for
        assistance, he meets Virgil, who offers to guide him through the depths of Hell and beyond. This marks the
        beginning of a transformative journey as they embark on a quest to understand the nature of sin, redemption,
        and divine justice. This intricate journey sets the tone for the rich allegorical explorations and profound
        reflections on the human condition that unfold throughout the text. (This is an automatically generated
        summary.) Show Less
        """
    categories = get_categories(test_case, summary)
    print(f"Categories: {categories}")

if '3' in selected or run_all:
    readability = calculate_readability_score(book_content)
    print(f"Readability: {readability}")

if '4' in selected or run_all:
    wiki_links = get_book_wikipedia_links(title, language)
    print(f"Book Wikipedia: {wiki_links}")

if '5' in selected or run_all:
    for author in authors:
        author_metadata = get_author_metadata(author['id'])
        wiki_link = get_author_wikipedia_link(author, author_metadata)
        print(f"Author Wikipedia: {wiki_link}")
