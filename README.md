## What It Does
The system runs once a month to process all books that have been published on Project Gutenberg since the last run (usually that means processing about 200 new books). For each of these new books we do 5 things: generate a summary using ChatGPT, assign the book to the appropriate "Main Categories" also using ChatGPT, calculate a readability score (Flesch–Kincaid readability test) try to find wikipedia links for the book and also try to find wikipedia links for the author(s).

## Architecture
- `main.py` is the main script that orchestrates the five-step pipeline for each book. It's very simple and straightforward. There's a separate file for each of the five steps: `summaries.py`, `categories.py`, `readability.py`, `wiki_for_books.py`, `wiki_for_authors.py`

To make the code easier to understand I added a comment at the very top of each of these files describing their logic in general terms. I recommend reading those comments before trying to understand the code itself.

**Results:** Results are saved in the `results/` directory in a file named after the current month. They are saved as sql-queries as requested by Greg. The idea was that these sql quries could then be directly run to put the results into the database and thereby online. Eric asked to get the results in their original format instead (i.e. not within sql), so I added `process_sql_results.py` which parses the original results out of the sql statemetns and saves them in the "processed_results" directory.

**Errors:** Errors are saved in the `errors/` directory in a file named after the current month.

**State & Data:**
- `latest_id.txt` — Tracks last processed book ID
- `categories.txt` — Master list of the 72 Main categories and their ids
- `done_authors.txt` — author_ids of those authors that already have a Wikipedia link on Gutenberg (avoiding duplication)

**Setup:** Add API keys (OpenAI, Serper, Perplexity) to `.env`, then `pip install -r requirements.txt`.

**Run:** `python main.py` processes books from the last saved ID to the latest available, saving SQL to `results/` and errors to `errors/` as said. latest_id.txt gets incremented with every processed book.

**Code Quality:** The code has been written in my limited free time and without the expectation that it would ever be shared with anyone. It's thus largely unedited and unrefined. I've done some basic clean-up of some parts of it, but not all.