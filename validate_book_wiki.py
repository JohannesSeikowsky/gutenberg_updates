"""Additional validation of Wikipedia links for books using Claude."""

import os
import re
import anthropic
from dotenv import load_dotenv
from utils import download_wikipedia_article

load_dotenv()


def validate_wiki_link(wiki_url: str, title: str, authors: str) -> bool:
    """Validate if Wikipedia article matches the book using Claude."""
    try:
        # Fetch Wikipedia content and truncate for validation
        validation_length = 3000
        content = download_wikipedia_article(wiki_url)[:validation_length]

        # Ask Claude if article matches the book
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Does this Wikipedia article match the work listed below?

WORK:
- Title: {title}
- Author(s): {authors}

WIKIPEDIA ARTICLE (first 2000 chars):
```
{content}
```

Is the Wikipedia article about this work? Ignore edition details (translations, volumes, annotations).

Respond:
VERDICT: [YES/NO]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASONING: [one very short sentence]"""
            }]
        )

        # Parse VERDICT from response
        answer = response.content[0].text
        verdict_match = re.search(r'VERDICT:\s*(YES|NO)', answer, re.IGNORECASE)
        return verdict_match and verdict_match.group(1).upper() == "YES"

    except Exception:
        return False


def validate_wiki_links(wiki_links: list[str], title: str, authors_str: str) -> list[str]:
    """Filter Wikipedia links to only those that match the book."""
    validated_links = []
    for url in wiki_links:
        if validate_wiki_link(url, title, authors_str):
            validated_links.append(url)
    return validated_links