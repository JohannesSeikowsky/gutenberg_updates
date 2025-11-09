## How It Works
The system runs monthly to process all books added to Project Gutenberg since the last run.
Specifically we're generating a summary for each book, assigning it to the appropriate "Main Categories", compute a readiblity score and attempt to find wikipedia links (for both the books themselves and their authors).

## Architecture
- `main.py` orchestrates the five-step pipeline for each book. Each of the five steps has its relevant code in one specific file:

- `summaries.py` — Generates 2-paragraph summaries via ChatGPT5 (chunks large books).
- `readability.py` — Calculates Flesch reading ease scores
- `categories.py` — Assigns books to predefined categories using GPT structured output
- `wiki_for_books.py` — Finds Wikipedia links via Google search + GPT verification
- `wiki_for_authors.py` — Locates author Wikipedia pages using Perplexity

**State & Data:**
- `latest_id.txt` — Tracks last processed book ID
- `done_authors.txt` — Prevents duplicate author processing
- `categories.txt` — Master list of 72 category IDs
- `results/` — Monthly SQL output files
- `errors/` — Monthly error logs


**Setup:** Add API keys (OpenAI, Serper, Perplexity) to `.env`, then `pip install -r requirements.txt`

**Run:** `python main.py` processes books from the last saved ID to the latest available, saving SQL to `results/` and errors to `errors/`