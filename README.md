## What It Does
The system runs once a month to process all books that have been newly published on Project Gutenberg since the last run (usually that's around 200 new books). For each of these new books we do 5 things: generate a summary (using Wikipedia article if available, otherwise from book content), assign the book to the appropriate "Main Categories" using ChatGPT, calculate a readability score (Flesch–Kincaid readability test), try to find wikipedia links for the book and finally also try to find wikipedia links for the author(s).

## Architecture
`main.py` is the main script that orchestrates this five-step pipeline for each book. It's deliberately simple and straightforward. There's a separate file for each of the five steps: `summaries.py` (book content summaries), `wiki_based_summaries.py` (Wikipedia-based summaries), `categories.py`, `readability.py`, `wiki_for_books.py` (includes two-layer validation), `wiki_for_authors.py`

The data that's necessary to run this pipeline is obtained by scraping the Project Gutenberg once for each book (see main.py). I suspect a better integration with the publishing process may be possible.

To make the code easier to understand I added an explanatory comment at the beginning of each of the most important files. I recommend reading those comments before trying to understand the code.

## Results
Results are saved in the `results/` directory in a file named after the current month. They are saved in sql-queries as requested by Greg. The idea was that these sql quries could then be directly run to put the results into the database and thereby online on gutenberg.org. Eric recently asked to get the results in their original format instead (i.e. not within sql), so I added `process_sql_results.py` which parses said results out of the sql and saves them in "processed_results/".

## Errors
Errors are saved in the `errors/` directory in a file named after the current month.

## State & Data
- `latest_id.txt` — Tracks the ID of the last processed book
- `categories.txt` — Master list of the 72 Main categories and their ids

## Tests
The code in `tests.py` runs the pipeline for a representative test case. Super minimalistic but still useful after changes to ensure the major functionalities still work.

## Setup
Add API keys (OpenAI, Serper and Perplexity) to `.env`, then `pip install -r requirements.txt`.

## Run
`python main.py` processes books chronologically in the manner described taking the starting ID from latest_id.txt (latest_id.txt then gets incremented with each processed book).

## ToDo
- Integration with the continual publishing process of new books. This is by far the most important thing!
- Maybe there's a better way than scraping to get the necessary data into the pipeline. Would seem like a natural part of the integration into the publishing process.
- I havent had time to thoroughly check whether the error logging logic does a solid job or could be improved.
- The two "wiki" scripts use different approaches for finding Wikipedia links. Maybe one approach is better than the other.
- tests.py could very easily be extended to run for more than just 1 test case
- `process_sql_results.py` can be made redudant by adjusting the saving functions

**Note: a LOT depends on the integration of this pipeline into the "normal" publishing process, which is why that's No1 on this list.**