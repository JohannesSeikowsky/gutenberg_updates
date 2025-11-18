## What It Does
The system runs once a month to process all books that have been newly published on Project Gutenberg since the last run (usually that's around 200 new books). For each of these new books we do 5 things: generate a summary using ChatGPT, assign the book to appropriate "Main Categories" also using ChatGPT, calculate a readability score (Flesch–Kincaid readability test), try to find wikipedia links for the book and finally try to find wikipedia links for the author(s).

## Architecture
`main.py` is the main script that orchestrates the five-step pipeline for each book. It's deliberately very simple and straightforward. There's a separate file for each of the five steps: `summaries.py`, `categories.py`, `readability.py`, `wiki_for_books.py`, `wiki_for_authors.py`

The data that's necessary to run this pipeline is obtained by scraping the Project Gutenberg page once for each book (lines 34-35 main.py). I suspect a better integration with the publishing process may be possible.

To make the code easier to understand I added a comment at the beginning of each of the main code files briefly stating what's being done in general terms. I recommend reading those comments before trying to understand the code.

## Results
Results are saved in the `results/` directory in a file named after the current month. They are saved in sql-queries as requested by Greg. The idea was that these sql quries could then be directly run to put the results into the database and thereby online. Eric asked to get the results in their original format instead (i.e. not within sql), so I added `process_sql_results.py` which parses them out of the sql and saves them in "processed_results/".

## Errors
Errors are saved in the `errors/` directory in a file named after the current month.

## State & Data
- `latest_id.txt` — Tracks the ID of the last processed book
- `categories.txt` — Master list of the 72 Main categories and their ids
- `done_authors.txt` — author_ids of those authors that already have a Wikipedia link on Gutenberg (to avoid duplication)

## Setup
Add API keys (OpenAI, Serper and Perplexity) to `.env`, then `pip install -r requirements.txt`.

## Run
`python main.py` processes books chronologically in the manner described taking the ID from latest_id.txt as the starting point (latest_id.txt gets incremented with every processed book).

## Code Quality
The code has been written in my limited free time and without the expectation that it would ever be shared with anyone. It's thus largely unedited and unrefined. I've done some basic clean-up of some parts of it, but not all.