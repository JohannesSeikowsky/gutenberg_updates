# Calculates readability scores of a book using the Flesch-Kincaid readability test.
# The exact score is then used to assign the book to a readability grade.

import textstat

def calculate_readability_score(book_content):
  """Calculate Flesch reading ease score for book content."""
  return textstat.flesch_reading_ease(book_content)


def get_readability_grade(score):
  """Get grade level and description for a readability score."""
  score_ranges = [
      (90, 100, "5th grade", "Very easy to read."),
      (80, 90, "6th grade", "Easy to read."),
      (70, 80, "7th grade", "Fairly easy to read."),
      (60, 70, "8th & 9th grade", "Neither easy nor difficult to read."),
      (50, 60, "10th to 12th grade", "Somewhat difficult to read."),
      (30, 50, "College-level", "Difficult to read."),
      (10, 30, "College graduate level", "Very difficult to read."),
      (0, 10, "Professional level", "Extremely difficult to read.")
  ]

  for min_val, max_val, grade, description in score_ranges:
      if min_val <= score <= max_val:
          return grade, description
  return None, None


def save_readability_sql(book_id, score, output_file):
  """Generate and append readability SQL statement to output file."""
  grade, description = get_readability_grade(score)
  sql = f"insert into attributes (fk_books,fk_attriblist,text,nonfiling) values ({book_id},908,'Reading ease score: {score:.1f} ({grade}). {description}',0);"
  with open(output_file, "a") as f:
    f.write(f"{sql}\n")