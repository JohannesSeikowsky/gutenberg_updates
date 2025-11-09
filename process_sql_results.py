
# insert into attributes (fk_books,fk_attriblist,text,nonfiling) values (76714,500,'https://en.wikipedia.org/wiki/The_Little_Review',0);
# insert into attributes (fk_books,fk_attriblist,text,nonfiling) values (76724,500,'https://en.wikipedia.org/wiki/The_Chase_of_the_Golden_Meteor https://fr.wikipedia.org/wiki/La_Chasse_au_m%C3%A9t%C3%A9ore',0);
# insert into author_urls (fk_authors, description, url) values (57752,'fi.wikipedia','https://fi.wikipedia.org/wiki/Matti_Kivek%C3%A4s');

{57752: "'fi.wikipedia', 'https://fi.wikipedia.org/wiki/Matti_Kivek%C3%A4s'"}
{76724: "'https://en.wikipedia.org/wiki/The_Chase_of_the_Golden_Meteor https://fr.wikipedia.org/wiki/La_Chasse_au_m%C3%A9t%C3%A9ore'"}
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
      # Save as JSONL
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
