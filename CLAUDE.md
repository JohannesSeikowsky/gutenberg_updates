# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated system that enriches Project Gutenberg books with metadata. It processes new books sequentially by ID, generating:
- AI-powered summaries (using OpenAI GPT)
- Readability scores (Flesch reading ease)
- Category assignments
- Wikipedia links for books and authors

All outputs are formatted as SQL INSERT statements for database integration.

## Environment Setup

**API Keys Required:**
- OpenAI API key
- Serper API key (for Google search)
- Perplexity API key

These should be stored in a `.env` file (see `.gitignore`).

**Installation:**
```bash
pip install -r requirements.txt
```

## Running the System

**Main script:**
```bash
python main.py
```

The script:
1. Reads the last processed book ID from `latest_id.txt`
2. Fetches the latest available book ID from gutenberg.org
3. Processes each book in sequence, generating SQL statements
4. Saves results to `results/update_MM_YY.txt`
5. Logs errors to `errors/errors_MM_YY.txt`
6. Updates `latest_id.txt` after each book

## Architecture

**Processing Pipeline (main.py):**
Each book goes through 5 steps sequentially with error handling:
1. Summary generation (`summaries.py`)
2. Wikipedia links for books (`wiki_for_books.py`)
3. Readability calculation (`readability.py`)
4. Category assignment (`categories.py`)
5. Wikipedia links for authors (`wiki_for_authors.py`)

**Key Components:**

- `utils.py`: Shared utilities for fetching book content, parsing Gutenberg pages, tracking state
- `summaries.py`: Uses GPT to generate 2-paragraph summaries. Chunks books >24k tokens and only summarizes the beginning
- `readability.py`: Calculates Flesch reading ease scores using textstat library
- `categories.py`: Uses GPT with structured output to assign books to predefined categories from `categories.txt`
- `wiki_for_books.py`: Google searches for Wikipedia links, uses GPT to verify correctness. Handles both English and non-English books
- `wiki_for_authors.py`: Fetches author info from Gutenberg, uses Perplexity to find Wikipedia pages. Tracks completed authors in `done_authors.txt` to avoid duplicates

**State Management:**
- `latest_id.txt`: Last successfully processed book ID
- `done_authors.txt`: Author IDs already processed (prevents duplicate API calls)

## Important Notes

- All API calls include delays (1-6 seconds) to avoid rate limiting
- Book content is fetched from `gutenberg.org/cache/epub/{id}/pg{id}.txt`
- Gutenberg boilerplate text is stripped using `cut_beginning()` and `cut_end()`
- The system is designed to run monthly and process all new books since last run
