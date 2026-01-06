# Generates a summary of a book using ChatGPT.
# For short books we feed in the entire book, for long books we feed in roughly the first 35 pages.
# This is necessary due to cost and context-size limitations.
# Read the prompting for a better understanding of how it works.

# One thing to realise is that what we're looking to put on the Gutenberg page is not
# actually an exhaustive summary of all the content of a book, but rathern an impression of it
# so that users can decide whether try a book or not. Kind of like a trailer to a movie.
# In that sense "summary" is not actually a very accurate term.

from openai import OpenAI
import tiktoken
import os
from dotenv import load_dotenv

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def count_tokens(text, encoding_name='cl100k_base'):
    """Count the number of tokens in a text."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def get_first_chunk(text, max_token_size, encoding_name="cl100k_base"):
    """Extract first chunk of text up to max_token_size tokens."""
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    first_chunk_tokens = tokens[:max_token_size]
    return encoding.decode(first_chunk_tokens)


def format_summary(summary):
    """Format summary for SQL insertion by replacing markdown, removing newlines, and escaping quotes."""
    # fixing common oddities sometimes returned by LLM
    formatted = summary.replace('*', '"').replace('_', '"').replace('"""', '"').replace('""', '"')
    # removing new lines because gutenberg website can't display newlines in HTML (unfortunately)
    formatted = formatted.replace("\n", " ")
    # add sql requirement to escape single quotes with an additional single quote
    formatted = formatted.replace("'", "''")
    return formatted


def summarise_beginning_of_book(title_and_author, text):
    """Generate two-paragraph summary from book's opening portion using GPT. To be used for long books."""
    system_prompt = {"role": "system", "content": """You are a helpful assistant that is very good at deriving an understanding of books based on their opening chapters. You are also very good at writing texts about those books based on your understanding that are useful to potential readers who need to decide whether a particular book is interesting to them or not."""}

    user_instruction = {"role": "user", "content": f"""You will be given the opening portion of a book. Read it very carefully to understand its content and derive an idea of the book in general. Based on your understanding write two paragraphs.

  The first paragraph should be concise and to-the-point. The first sentence should include:
  - the title of the book and name of the author (if provided), which is: {title_and_author}.
  - what type of book it is (e.g. novel, scientific publication, historical account, collection of short stories etc.)
  - what general time period the book was probably written in (e.g. early 19th century, mid-19th century, late 19th century, 14th century). Only refer to general time periods like that, do NOT use specific years and dates!

  Overall the general structure of the first sentence should be exactly this: "<title_name>" by <author_name> is a <book_type> written in <time_period>.
  However only include these values if you're reasonably sure. If there is no author_name or you can't reasonably tell the time_period for example, just don't include them.

  After that first sentence finish the first paragraph with a concise statement about what the likely topic of the book is. If it's a fiction work mention the main character(s) if you can (but avoid spoiler alerts). The goal of this is that the reader gets a first impression of the book that he or she can use to decide whether the book seems interesting or not.
  As said, this first paragraph should be concise. 4 sentences or less is best.

  Here are some EXAMPLES of how this first paragraph should principally look like:
  1) "Adventures of Sherlock Holmes" by Sir Arthur Conan Doyle is a collection of detective stories written during the late 19th century. The book follows the brilliant detective Sherlock Holmes and his companion Dr. John Watson as they solve various cases.
  2) "The Elements of Style" by William Strunk Jr. and E.B. White is a guidebook on English language usage written in the mid-20th century. The book lays out the principles of clear and concise writing, offering rules and recommendations for effective communication.
  3) "The Art of War" by Sun Tzu is a treatise on military strategy written in the 5th century BC. The book lays out principles of military strategy and tactics, emphasizing the importance of intelligence, deception, and the use of terrain.
  4) "Introduction to Algorithms" by Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, and Clifford Stein is a comprehensive computer science textbook written in the late 20th century. The book follows a structured approach to teaching algorithms, covering a wide range of topics from basic data structures to advanced algorithmic techniques.
  5) "Vesper Talks to Girls" by Laura A. Knott is a collection of motivational addresses written in the early 20th century. The book compiles talks given to young women at Bradford Academy, addressing aspects of personal development, friendships, and the importance of character.

  After you finished this first short paragraph, please write a second paragraph with a concise summary of the book's opening portion that I will provide you with.
  In that second paragraph focus on the actual content of that opening part (i.e. the characters, the content, the storyline etc.).
  Make sure to cover only the main points and main ideas, whilst avoiding any unnecessary information or repetition.
  Overall this summary should be quite brief.
  Make it very clear that this is a summary of only the opening portion of the book. Do that by starting the paragraph with a variation of "The beginning of ..." or "The opening of ..." or "At the start of ...".

  In your writing use simple, clear, concise and expressive language.
  State the name of the book and the author's name only once throughout your response.
  In some cases there may be a more appropriate word than "book" to refer to the work I'll give you. Use your judgement to use appropriate terminology. Always write in English. And never include any urls in your response."""}

    assistant_reply = {"role": "assistant", "content": "Understood! Please provide the opening portion of the book and I will follow your instructions."}
    book_content = {"role": "user", "content": f"START OF BOOK BEGINNING: \n{text}\nEND OF BOOK BEGINNING"}

    messages = [system_prompt, user_instruction, assistant_reply, book_content]
    response = openai_client.chat.completions.create(model="gpt-5.2", messages=messages)
    return response.choices[0].message.content


def summarise_entire_book(title_and_author, text):
    """Generate two-paragraph summary from entire book using GPT. To be used for short books."""
    system_prompt = {"role": "system", "content": """You are a helpful assistant that is very good at reading and understanding books. You are also very good at writing texts about those books based on your understanding that are useful to potential readers who need to decide whether a particular book is interesting to them or not."""}

    user_instruction = {"role": "user", "content": f"""
  You will be given the entire book. Read it very carefully to understand its content. Based on your understanding write two paragraphs.

  In the first paragraph briefly lay out some high-level information about the book in general. Specifically include the title and the author (if available) of the book which is this: "{title_and_author}". Include it exactly like this, do NOT change it. Also include what type of book it is (e.g. novel, biography, crime fiction, scientific. publication, collection of short stories, historical account etc.) and what time period the book was probably written in (e.g. Victorian era, early 20th century etc.). Do NOT use specific years but instead use wider time spans. So for example, rather than saying "1886", you could say "late 1800s" or "in the late 19th century". Moreover include a very concise statement what the likely topic of the book is.

  Here are some EXAMPLES of how that first paragraph should principally look like
  1) "Adventures of Sherlock Holmes" by Sir Arthur Conan Doyle is a collection of detective stories written during the late 19th century. The book follows the brilliant detective Sherlock Holmes and his companion Dr. John Watson as they solve various cases.
  2) "The Elements of Style" by William Strunk Jr. and E.B. White is a guidebook on English language usage written in the mid-20th century. The book lays out the principles of clear and concise writing, offering rules and recommendations for effective communication.
  3) "The Art of War" by Sun Tzu is a treatise on military strategy written in the 5th century BC. The book lays out principles of military strategy and tactics, emphasizing the importance of intelligence, deception, and the use of terrain.
  4) "Introduction to Algorithms" by Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, and Clifford Stein is a comprehensive computer science textbook written in the late 20th century. The book follows a structured approach to teaching algorithms, covering a wide range of topics from basic data structures to advanced algorithmic techniques.
  5) "Vesper Talks to Girls" by Laura A. Knott is a collection of motivational addresses written in the early 20th century. The book compiles talks given to young women at Bradford Academy, addressing aspects of personal development, friendships, and the importance of character.

  After you finished that first paragraph, please write a concise summary of the book in the second paragraph.
  Focus on the actual content of the book (i.e. the characters, the content, the storyline etc.).
  Make sure to cover only the main points and main ideas, whilst avoiding any unnecessary information or repetition.
  Overall this summary should be relatively brief.

  In your writing use simple, clear, concise and expressive language.
  State the name of the book and the author's name only once throughout your response. Always write in English. And never include any urls in your response."""}

    assistant_reply = {"role": "assistant", "content": "Understood! Please provide the book and I will follow your instructions."}
    book_content = {"role": "user", "content": f"START OF BOOK: \n{text}\nEND OF BOOK"}

    messages = [system_prompt, user_instruction, assistant_reply, book_content]
    response = openai_client.chat.completions.create(model="gpt-5.2", messages=messages)
    return response.choices[0].message.content


def summarise_book(book_content, title):
    """Generate formatted summary for book, using full text or opening portion based on length."""
    chunk_size = 24000
    print("Summarising:", title)

    if count_tokens(book_content) > chunk_size:
        beginning_of_book = get_first_chunk(book_content, chunk_size)
        summary = summarise_beginning_of_book(title, beginning_of_book)
    else:
        summary = summarise_entire_book(title, book_content)

    return format_summary(summary)


def save_summary_sql(book_id, summary, output_file):
    """Append SQL INSERT statement for book summary to output file."""
    note = " (This is an automatically generated summary.)"
    sql = f"insert into attributes (fk_books,fk_attriblist,text,nonfiling) values ({book_id},520,'{summary}{note}',0);"

    with open(output_file, "a") as f:
        f.write(f"{sql}\n")


def is_valid_wikipedia_link_for_summary(wiki_links):
    """Check if Wikipedia links are suitable for summary generation (placeholder)."""

    # llm check returns positive
    # if there are two you pick the longer one.
    # too short ...
    # test whether good for summary generation ...

    return bool(wiki_links)



def summarise_book_from_wikipedia(wiki_links, title):
    """Generate book summary from Wikipedia page content (placeholder)."""
    # TODO: Implement Wikipedia content fetching and summarization
    # Steps to implement:
    # 1. Fetch content from wiki_links[0] (primary link)
    # 2. Extract relevant sections (intro, plot, overview)
    # 3. Pass to GPT for summarization (similar to current approach)
    # 4. Format and return

    # For now, return formatted placeholder text
    placeholder = f"[Wikipedia-based summary for '{title}' - To be implemented]"
    return format_summary(placeholder)
