# Assigns a book to one or more predefined categories using ChatGPT.
# We have 72 predefined categories in total listed in categories.txt.
# We're using a schema to force ChatGPT to pick only from our predefined list and return the result as a list of strings.

from openai import OpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _load_categories():
    """Parse categories.txt and return: name-to-id dict, category names list, newline-joined category names."""
    with open("categories.txt") as f:
        id_name_pairs = [line.strip().split(", ", 1) for line in f]

    name_to_id = {name: cat_id for cat_id, name in id_name_pairs}  # Dict for looking up IDs
    category_names = [name for _, name in id_name_pairs]  # List of names
    category_names_text = "\n".join(category_names)  # Newline-joined text for prompts
    return name_to_id, category_names, category_names_text

name_to_id, category_names, category_names_text = _load_categories()


system_prompt_template = """You are an expert at choosing appropriate categories for books. You do this by thoroughly reading the summary of a book to cultivate an understanding of what the book is about. In doing so you think critically about what the central topic or topics of the book are and what the peripheral topic or topics are. Just because certain "matching words" appear in the summary does not mean that the book is about that topic. You must read the summary carefully and think about what the book is actually about. Then and only then you pick appropriate categories for the book from this particular list of available categories:
    <categories>
    {category_names_text}
    </categories>
    """

user_instruction = """I will give you the summary of a book. Your job is to read that summary thoroughly and mull it over. Then, based on your understanding, use your best judgement to pick the most appropriate categories from the list of categories.
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

assistant_acknowledgment = "Ok, please give me the summary of the book. I will read it thoroughly and based on my understanding pick the categories that are relevant for this book. When picking the categories I will bear in mind that these will be used by people to find books that are relevant to them. So I'll make sure to pick categories according to what people may expect to find in each category."


def _build_response_schema():
    """Build the JSON schema for GPT response."""
    return {
        "name": "book_categories",
        "schema": {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "description": "Chosen category or categories for the particular book.",
                    "items": {"type": "string", "enum": category_names}
                }
            },
            "required": ["categories"],
            "additionalProperties": False
        },
        "strict": True
    }


def get_categories(book_id, summary):
    """Assigns book to categories using GPT based on summary."""
    system_prompt = system_prompt_template.format(category_names_text=category_names_text)

    response = openai_client.beta.chat.completions.parse(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_instruction},
            {"role": "assistant", "content": assistant_acknowledgment},
            {"role": "user", "content": f"<summary>{summary}</summary>"}
        ],
        response_format={"type": "json_schema", "json_schema": _build_response_schema()}
    )

    if not response.choices or not response.choices[0].message.content:
        raise ValueError(f"Empty response from OpenAI for book {book_id}")

    return json.loads(response.choices[0].message.content)["categories"]


def save_categories_sql(book_id, categories, output_file):
    """Writes SQL INSERT statements for book-category mappings to output file."""
    category_ids = [name_to_id[name] for name in categories]

    with open(output_file, "a") as f:
        for category_id in category_ids:
            f.write(f"insert into mn_books_bookshelves (fk_books,fk_bookshelves) values ({book_id},{category_id});\n")