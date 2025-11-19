# Originally results were saved in sql-queries as requested by Greg. 
# Eric asked to get the results in their original format instead (i.e. not within sql)
# This script parses the results out of the sql and saves them in "processed_results/".

import json
import os

# Create directory if it doesn't exist
os.makedirs("processed_results/summaries", exist_ok=True)
os.makedirs("processed_results/readability", exist_ok=True)
os.makedirs("processed_results/categories", exist_ok=True)
os.makedirs("processed_results/author_wikipedia", exist_ok=True)
os.makedirs("processed_results/book_wikipedia", exist_ok=True)


with open("results/update_10_25.txt", "r") as f:
  lines = f.readlines()

# summaries
for line in lines:
  try:
    if "(This is an automatically generated" in line:
      summary = line.split("520,'")[1].split("',0);")[0]
      id = int(line.split("values (")[1].split(",520")[0])
      with open("processed_results/summaries/summaries_10_25.jsonl", "a") as jsonl_file:
        jsonl_file.write(json.dumps({id: summary}) + "\n")
  except Exception as e:
    print(f"Error processing summary line: {e}")
    print(f"Line: {line[:100]}...")

# reading ease scores
for line in lines:
  try:
    if "Reading ease score" in line:
      id = int(line.split("values (")[1].split(",908")[0])
      score = line.split("908,'")[1].split("',0);")[0]
      
      with open("processed_results/readability/readability_10_25.jsonl", "a") as jsonl_file:
        jsonl_file.write(json.dumps({id: score}) + "\n")
  except Exception as e:
    print(f"Error processing readability line: {e}")
    print(f"Line: {line[:100]}...")

# categories
for line in lines:
  try:
    if "mn_books_bookshelves" in line:
      id = int(line.split("values (")[1].split(",")[0])
      category_id = int(line.split(",")[-1].split(");")[0])

      with open("processed_results/categories/categories_10_25.jsonl", "a") as jsonl_file:
        jsonl_file.write(json.dumps({id: category_id}) + "\n")
  except Exception as e:
    print(f"Error processing category line: {e}")
    print(f"Line: {line[:100]}...")

# author wikis
for line in lines:
  try:
    if "author_urls" in line:
      id = int(line.split("values (")[1].split(",'")[0])
      description = line.split(",'")[1].split("',")[0]
      link = line.split(",'")[-1].split("');")[0]

      with open("processed_results/author_wikipedia/author_wikipedia_10_25.jsonl", "a") as jsonl_file:
        jsonl_file.write(json.dumps({id: f"{description},{link}"}) + "\n")
  except Exception as e:
    print(f"Error processing author wiki line: {e}")
    print(f"Line: {line[:100]}...")

# book wikis
for line in lines:
  try:
    if "wikipedia" in line and "author_urls" not in line:
      id = int(line.split("values (")[1].split(",500")[0])
      links = line.split("500,'")[1].split("',0);")[0]

      with open("processed_results/book_wikipedia/book_wikipedia_10_25.jsonl", "a") as jsonl_file:
        jsonl_file.write(json.dumps({id: links}) + "\n")
  except Exception as e:
    print(f"Error processing book wiki line: {e}")
    print(f"Line: {line[:100]}...")
