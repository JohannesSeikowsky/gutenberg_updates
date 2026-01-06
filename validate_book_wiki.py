"""Additional validation of Wikipedia links for books using Claude."""

import os
import re
from urllib.parse import unquote
import requests
import anthropic
from dotenv import load_dotenv

load_dotenv()


def validate_wiki_link(wiki_url: str, title: str, authors: str) -> bool:
    """Validate if Wikipedia article matches the book using Claude."""
    try:
        # Extract page title from URL
        match = re.search(r'(https?://[a-z]{2,3}\.wikipedia\.org)/wiki/(.+)$', wiki_url)
        if not match:
            return False

        base_url = match.group(1)
        page_title = unquote(match.group(2))

        # Fetch Wikipedia content
        response = requests.get(
            f"{base_url}/w/api.php",
            params={
                'action': 'query',
                'format': 'json',
                'prop': 'extracts',
                'explaintext': True,
                'redirects': 1,
                'titles': page_title
            },
            headers={'User-Agent': 'WikiValidation/1.0 (Educational project; Contact: joseikowsky@gmail.com)'},
            timeout=30
        )

        data = response.json()
        pages = data.get('query', {}).get('pages', {})
        if not pages:
            return False

        page = next(iter(pages.values()))
        content = page.get('extract', '')[:2000]

        if not content:
            return False

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