"""Generate a single Wikipedia article summary using Claude API."""

import anthropic
import os
from dotenv import load_dotenv
from utils import download_wikipedia_article

load_dotenv()
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = "You are skilled at writing compelling, teaser-style introductions for literary and artistic works that intrigue readers without revealing everything."

USER_PROMPT_TEMPLATE = """The official title of this work on Project Gutenberg is: "{gutenberg_title}"

Please use this as the authoritative title in your introduction, even if the Wikipedia article uses a different title (this may occur due to language differences or variations in naming).

I'm going to give you the first 1200 words of the Wikipedia article of this work.
Write an introduction-text for it that works like a movie trailer — giving a sense of what the work is about without revealing too much i.e. avoid spoilers. Write between 80-90 words. Do not exceed 90 words.

If possible, the first sentence should follow this pattern: "(title)" by (author/composer) is a (type of work) written/published/composed in (time period).
Note: The time period should be as specific as possible. If you have a specific year use that. If you have a decade or century, use that. If you don't have relevant information, please omit it.
Base your word choice of using "written", "published", or "composed" on the content of the Wikipedia article.

Examples:
- "To Kill a Mockingbird" by Harper Lee is a novel written in 1960.
- "Symphony No. 9" by Ludwig van Beethoven is a symphony composed in 1824.
- "Letters to a Young Poet" by Rainer Maria Rilke is a collection of letters written between 1902-1908.

Keep your writing very simple and straightforward. Avoid long sentences and unnecessarily complex language. Be clear and direct.

Make sure to base EVERYTHING on the content of the Wikipedia article! Do NOT add any information that is not presented in the Wikipedia article.

Always write in English, even if the Wikipedia article is in a different language.

On occasion it is possible that the Wikipedia article does not have enough relevant information for you to write a reasonable introduction-text.
i.e. it doesn't allow you to write a summary that conveys what the work is principally about.
If that is so, please return "insufficient information"

<WIKIPEDIA ARTICLE>
{article_text}
</WIKIPEDIA ARTICLE>"""


def truncate_to_words(text, word_limit):
    """Truncate text to specified number of words."""
    words = text.split()
    if len(words) <= word_limit:
        return text
    return ' '.join(words[:word_limit])


def select_wikipedia_article(wiki_links, min_word_count=280):
    """Select the longest Wikipedia article from wiki_links, excluding articles shorter than min_word_count."""
    if not wiki_links:
        return None

    # Step 1: Download all articles and exclude those shorter than min_word_count
    articles_meeting_minimum = []

    for url in wiki_links:
        try:
            article_text = download_wikipedia_article(url)
            word_count = len(article_text.split())

            # Exclude articles shorter than minimum
            if word_count >= min_word_count:
                articles_meeting_minimum.append((article_text, word_count))
        except Exception:
            # Skip articles that fail to download, continue with others
            continue

    if not articles_meeting_minimum:
        return None

    # Step 2: Pick the longest article from remaining candidates
    longest_article = max(articles_meeting_minimum, key=lambda x: x[1])
    return longest_article[0]


def generate_wiki_based_summary(article_text, gutenberg_title):
    """Generate a summary for a single article using Claude API."""
    truncated = truncate_to_words(article_text, 1200)
    prompt = USER_PROMPT_TEMPLATE.format(gutenberg_title=gutenberg_title, article_text=truncated)

    message = anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text
