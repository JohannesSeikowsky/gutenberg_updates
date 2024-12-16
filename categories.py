from openai import OpenAI
from pydantic import BaseModel, Field
from enum import Enum
from typing import Literal
import time
from utils import *
import random
import json

openai_client = OpenAI(api_key="REDACTED_API_KEY")

categories = open("categories.txt").read()
categories_list = categories.split("\n")

system_prompt = "Your job is to pick the most appropriate category for a certain book that I will tell you about. If appropriate you can also choose two categories for a certain book. If you're unsure what the appropriate category for a book is pick the 'Other' category."

prompt = f"""I will give you the title of a book and the name of its author (if available) and also a summary of that book. Your job is to consider the books title and read it's summary thoroughly and based on your derived understanding decide what the most appropriate category for the book is. If there are two categories that would be appropriate you can also pick two. Here is the list of the categories that you can pick from:

<categories>
{categories}
</categories>
"""

assistant_reply = "Ok, please give me the title, author and summary of the book. Based on that information I will pick one or two most apprppriate categories for the book from the list of categories."


schema = {
  "name": "book_categories",
  "schema": {
    "type": "object",
    "properties": {
      "categories": {
        "type": "array",
        "description": "Categories from which to pick the one or two most appropriate for a particular book.",
        "items": {
          "type": "string",
          "enum": categories_list
        },
      }
    },
    "required": [
      "categories"
    ],
    "additionalProperties": False
  },
  "strict": True
}

# maxitems?



def get_categories(book_id, summary):
  try:
    title_and_author = fetch_title_and_author_from_website(book_id)
    book_info = f"<title_and_author> {title_and_author} </title_and_author> \n <summary> {summary} </summary>"
    
    completion = openai_client.beta.chat.completions.parse(
      model="gpt-4o",
      messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": assistant_reply},
                {"role": "user", "content": book_info}
               ],
      response_format={"type": "json_schema", "json_schema": schema}
    )
    category_choice = json.loads(completion.choices[0].message.content)["categories"]
    return category_choice
  except Exception as e:
    print(e)


def save_categories(book_id, categories):
  ids = open("categories_ids.txt", "r").read().split("\n")
  ids = {category.split(", ")[1]: category.split(", ")[0] for category in ids}
  category_ids = [ids[category] for category in categories]

  for each in category_ids:
    with open("./results/categories.txt", "a") as f:
      f.write(f"insert into mn_books_bookshelves (fk_books,fk_bookshelves) values ({book_id},{each});\n")  
  return category_ids