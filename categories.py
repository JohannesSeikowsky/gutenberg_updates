# Assigns Project Gutenberg books to predefined categories using GPT and outputs SQL INSERT statements.

from openai import OpenAI
from utils import *
import json
import os
from dotenv import load_dotenv

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Parse the categories and their ids into required structures
with open("categories.txt") as f:
    parsed = [line.strip().split(", ", 1) for line in f if line.strip() and line.split(", ")[0].isnumeric()]

category_name_to_id = {name: id for id, name in parsed}
categories_list = [name for _, name in parsed]
categories = "\n".join(categories_list)


def get_categories(book_id, summary):
    system_prompt = f"""You are an expert at choosing appropriate categories for books. You do this by thoroughly reading the summary of a book to cultivate an understanding of what the book is about. In doing so you think critically about what the central topic or topics of the book are and what the peripheral topic or topics are. Just because certain "matching words" appear in the summary does not mean that the book is about that topic. You must read the summary carefully and think about what the book is actually about. Then and only then you pick appropriate categories for the book from this particular list of available categories:

    <categories>
    {categories}
    </categories>
    """

    prompt = f"""I will give you the summary of a book. Your job is to read that summary thoroughly and mull it over. Then, based on your understanding, use your best judgement to pick the most appropriate categories from the list of categories.

    The purpose of this is that the book will be displayed on a website that has these particular categories. Bear that in mind when picking the categories. So if you assign a category to a book it should be in such a way that if a website user were to browse that category on the website, he/she should NOT be surprised to find that book in that category. So it's important that you assign each book to the categories that make the most sense in light of what the book is about.

    Think sceptically and carefully about what categories are actually appropriate. For example, if a certain book is about "animal carvings" that book may appropriately assigned to "Art" but not to "Nature/Gardening/Animals". Also be careful to distinguish between "Literature" works and "History" works. By "Literature" we in general mean fictional writing. Whilst "History" is non-fictional writing about historical events/occurances.

    The category "How To ..." is for books that centrally give practical instruction or guidance for a certain task/endeavour.

    The "Classics of Literature" category is for the famous and significant works like "Moby Dick", "The Catcher in the Rye", "The Illiad" etc.

    The "Biographies" category is for all works that are generally biographical in nature, not only those that are written specifically as "pure" biographies. Diaries, personal journals etc. should therefore be included.

    The "Journals" category is for magazines and publications, not personal journals.

    If a book can reasonably be assigned into the categories of "American Literature", "British Literature", "German Literature", "French Literature" or "Russian Literature" in addition to what type of literature it is, then it should be assigned to both.

    The categories "Literature - Other" and "History - Other" are exclusively for history and literature books that do NOT fit into any of the other literature or history categories respectively.
    For example, if a book is assigned to "History - Warfare" (or any other history category), do NOT assign it to "History - Other" as well. Another example, if a book is assigned to "Poetry" (or any other literature category), do NOT assign it to "Literature - Other" as well.
    """

    assistant_reply = "Ok, please give me the summary of the book. I will read it thoroughly and based on my understanding pick the categories that are relevant for this book. When picking the categories I will be bear in mind that these will be used to by people to find books that are relevant to them. So I'll make sure to pick categories according to what people may be expect to find in each category."

    schema = {
        "name": "book_categories",
        "schema": {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "description": "Chosen category or categories for the particular book.",
                    "items": {
                        "type": "string",
                        "enum": categories_list
                    }
                }
            },
            "required": [
                "categories"
            ],
            "additionalProperties": False
        },
        "strict": True
    }

    completion = openai_client.beta.chat.completions.parse(
        model="gpt-5",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": assistant_reply},
            {"role": "user", "content": f"<summary> {summary} </summary>"}
        ],
        response_format={"type": "json_schema", "json_schema": schema}
    )

    if not completion.choices or not completion.choices[0].message.content:
        raise ValueError(f"Empty response from OpenAI for book {book_id}")

    category_choice = json.loads(completion.choices[0].message.content)["categories"]
    return category_choice


def save_categories(book_id, chosen_categories, output_file):
    category_ids = [category_name_to_id[category] for category in chosen_categories]

    with open(output_file, "a") as f:
        for category_id in category_ids:
            f.write(f"insert into mn_books_bookshelves (fk_books,fk_bookshelves) values ({book_id},{category_id});\n")
    return category_ids