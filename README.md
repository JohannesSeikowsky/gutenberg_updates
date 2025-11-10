## How It Works
The system runs monthly to process all books added to Project Gutenberg since the last run.
Specifically we're generating a summary for each book, assigning it to the appropriate "Main Categories", compute a readiblity score and attempt to find wikipedia links (for both the books themselves and their authors).

## Architecture
- `main.py` orchestrates the five-step pipeline for each book. Each of the five steps has its relevant code in one specific file:

- `summaries.py` — Generates 2-paragraph summaries using ChatGPT5. For small books, the entire book is fed in. For large books, roughly the first 30 pages or so are fed in. The prompting differs between the two cases.
- `readability.py` — Calculates Flesch reading ease scores
- `categories.py` — Assigns books to predefined categories using GPT structured output
- `wiki_for_books.py` — Finds Wikipedia links via Google search + GPT verification
- `wiki_for_authors.py` — Locates author Wikipedia pages using Perplexity

note - Perplexity is only used for wiki_for_authors and not for wiki_for_books, because I only had the idea that this could be done after wiki_for_books was already implemented.

**Results:** The results are saved in the results/ directory in a file named after the current month. They are saved as sql-queries (as requested by Greg). If desired process_sql_ressults.py can be used to parse the actual results out of their sql queries.

**State & Data:**
- `latest_id.txt` — Tracks last processed book ID
- `categories.txt` — Master list of 72 category IDs
- `done_authors.txt` — author_ids of those authors that already have a wikipedia link on Gutenberg (avoiding duplicate processing)
- `results/` — Monthly SQL output files
- `errors/` — Monthly error logs

**Setup:** Add API keys (OpenAI, Serper, Perplexity) to `.env`, then `pip install -r requirements.txt`

**Run:** `python main.py` processes books from the last saved ID to the latest available, saving SQL to `results/` and errors to `errors/`

**Code Quality:** This code has been written in my limited free time and with the expectation that only I would work on it. As a consequence large parts of it are unedited/unrefined. But it works. Eric asked me to share the code anyway.