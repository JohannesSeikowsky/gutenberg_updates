## What It Does
The system runs once a month to process all books that have been newly published on Project Gutenberg since the last run (usually that's around 200 new books). For each of these new books we do 5 things: generate a summary using ChatGPT, assign the book to appropriate "Main Categories" also using ChatGPT, calculate a readability score (Flesch–Kincaid readability test), try to find wikipedia links for the book and finally try to find wikipedia links for the author(s).

## Architecture
`main.py` is the main script that orchestrates the five-step pipeline for each book. It's deliberately very simple and straightforward. There's a separate file for each of the five steps: `summaries.py`, `categories.py`, `readability.py`, `wiki_for_books.py`, `wiki_for_authors.py`

The data that's necessary to run this pipeline is obtained by scraping the Project Gutenberg once for each book (lines 34-35 main.py). I suspect a better integration with the publishing process may be possible.

To make the code easier to understand I added a comment at the beginning of each of the most important files briefly explaining what's being done in general terms. I recommend reading those comments before trying to understand the code.

## Results
Results are saved in the `results/` directory in a file named after the current month. They are saved in sql-queries as requested by Greg. The idea was that these sql quries could then be directly run to put the results into the database and thereby online. Eric asked to get the results in their original format instead (i.e. not within sql), so I added `process_sql_results.py` which parses them out of the sql and saves them in "processed_results/".

## Errors
Errors are saved in the `errors/` directory in a file named after the current month.

## State & Data
- `latest_id.txt` — Tracks the ID of the last processed book
- `categories.txt` — Master list of the 72 Main categories and their ids

## Tests
The code in `tests.py` runs the pipeline for a representative test case. Super minimalistic but still useful to run after changes to ensure the major functionalities still work.

## Setup
Add API keys (OpenAI, Serper and Perplexity) to `.env`, then `pip install -r requirements.txt`.

## Run
`python main.py` processes books chronologically in the manner described taking the ID from latest_id.txt as the starting point (latest_id.txt gets incremented with every processed book).

## ToDo
- Integration with the continual publishing process of new books. This is the most important thing by far!!
- Maybe there's a better way than scraping to get the necessary data into the pipeline. 
- I havent had time to thoroughly check whether the error recording logic does a solid job.
- The two "wiki" scripts use different approaches for finding Wikipedia links. Maybe one approach is better than the other.
- Once we have code that generates summaries based on Wikipedia articles for those books that have them, there should be a branching logic since those books then obviously won't need a summary generated with the current method.
- tests.py could easily be extended to run for more than just 1 test case