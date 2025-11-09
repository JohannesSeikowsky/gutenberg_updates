import textstat
import requests
from utils import get_latest_book_id, cut_beginning, cut_end


def calculate_readability(book_id):
  url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
  book = requests.get(url).text
  book = cut_beginning(book)
  book = cut_end(book)
  reading_score = textstat.flesch_reading_ease(book)
  # print(f"Score: {reading_score}")
  return reading_score


def generate_sql(book_id, score):
  """ generate a SQL query for a given book book_id and reading ease score. """
  score = float(score)

  ranges = [
      (90, 100, "5th grade", "Very easy to read."),
      (80, 90, "6th grade", "Easy to read."),
      (70, 80, "7th grade", "Fairly easy to read."), 
      (60, 70, "8th & 9th grade", "Neither easy nor difficult to read."),
      (50, 60, "10th to 12th grade", "Somewhat difficult to read."),
      (30, 50, "College-level", "Difficult to read."),
      (10, 30, "College graduate level", "Very difficult to read."),
      (0, 10, "Professional level", "Extremely difficult to read.")
  ]

  for min_score, max_score, grade, description in ranges:
      if min_score <= score <= max_score:
          return f"insert into attributes (fk_books,fk_attriblist,text,nonfiling) values ({book_id},908,'Reading ease score: {score:.1f} ({grade}). {description}',0);"


def save_readability(book_id, readability_score, file):
  sql = generate_sql(book_id, readability_score)
  with open(file, "a") as f:
    f.write(f"{sql}\n")


# r = generate_sql(76687, calculate_readability(76687))
# print(r)