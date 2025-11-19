# Generates a summary of a book using ChatGPT.
# For short books we feed in the entire book, for long books we feed in roughly the first 35 pages.
# This is necessary due to cost and context-size limitations.
# Read the prompting for a better understanding of how it works.

# One thing to realise is that what we're looking to put on the Gutenberg page is not
# actually an exhaustive summary of the content of a book, but rathern an impression of it
# so that users can decide whether try a book or not. Kind of like a trailer for a movie.
# In that sense "summary" is not actually a very accurate term.

from openai import OpenAI
import tiktoken
import json
import os
from dotenv import load_dotenv
from utils import *

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_first_chunk(text, max_token_size, encoding_name="cl100k_base"):
  encoding = tiktoken.get_encoding(encoding_name)
  tokens = encoding.encode(text)

  # Initialize variables
  chunks = []
  current_chunk = []

  # Loop through the tokens and create chunks
  for token in tokens:
      current_chunk.append(token)
      if len(current_chunk) >= max_token_size:
          chunks.append(current_chunk)
          current_chunk = []

  # Add the last chunk if it exists
  if current_chunk:
      chunks.append(current_chunk)

  # Decode the tokens back into strings
  chunked_texts = [encoding.decode(chunk) for chunk in chunks]
  first_chunk = chunked_texts[0]
  return first_chunk


def count_tokens(text, encoding_name='cl100k_base'):
  try:
      encoding = tiktoken.get_encoding(encoding_name)
      tokens = encoding.encode(text)
      return len(tokens)

  except ValueError as e:
      print(f"Error: {e}")
      return None
    

def summarise_beginning_of_book(title_and_author, text):
    system_prompt = {"role": "system", "content": """You are a helpful assistant that is very good at deriving an understanding of books based on their opening chapters. You are also very good at writing texts about those books based on your understanding that are useful to potential readers who need to decide whether a particular book is interesting to them or not."""}
  
    prompt1 = {"role": "user", "content": f"""You will be given the opening portion of a book. Read it very carefully to understand its content and derive an idea of the book in general. Based on your understanding write two paragraphs.
  
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
  
  In you writing use simple, clear, concise and expressive language.
  State the name of the book and the author's name only once throughout your response.
  In some cases there may be a more apporpriate word than "book" to refer to the work I'll give you. Use your judgement to use appropriate terminology. Always write in English. And never include any urls in your response."""}
  
    prompt2 = {"role": "assistant", "content": "Understood! Please provide the opening portion of the book and I will follow your instructions."}
  
    prompt3 = {"role": "user", "content": "START OF BOOK BEGINNING: \n" + text + "\nEND OF BOOK BEGINNING"}
    response = openai_client.chat.completions.create(model="gpt-5", messages=[system_prompt, prompt1, prompt2, prompt3])
    response = response.choices[0].message.content
    return response


def summarise_entire_book(title_and_author, text):
  system_prompt = {"role": "system", "content": """You are a helpful assistant that is very good at reading and understanding books. You are also very good at writing texts about those books based on your understanding that are useful to potential readers who need to decide whether a particular book is interesting to them or not."""}
  prompt1 = {"role": "user", "content": f"""
  You will be given the entire book. Read it very carefully to understand its content. Based on your understanding write two paragraphs.

  In the first paragraph briefly lay out some high-level information about the book in general. Specifically include the title and the author (if available) of the book which is this: "{title_and_author}". Include it exactly like this, do NOT change it. Also include what type of book it is (e.g. novel, biography, crime fiction, scientific. publication, collection of short stories, historical account etc.) and what time period the book was probably written in (e.g. Victorian era, early 20th century etc.). Do NOT use specific years but instead use wider time spans. So for example, rather than saying "1886", you could say "late 1800s" or "in the late 19th century". Moreover include a very concise statement what the likely topic of the book is.

  Here are some EXAMPLES of how that first paragraph should principally look like
  1) "Adventures of Sherlock Holmes" by Sir Arthur Conan Doyle is a collection of detective stories written during the late 19th century. The book follows the brilliant detective Sherlock Holmes and his companion Dr. John Watson as they solve various cases.
  2) "The Elements of Style" by William Strunk Jr. and E.B. White is a guidebook on English language usage written in the mid-20th century. The book lays out the principles of clear and concise writing, offering rules and recommendations for effective communication.
  3) "The Art of War" by Sun Tzu is a treatise on military strategy written in the 5th century BC. The book lays out principles of military strategy and tactics, emphasizing the importance of intelligence, deception, and the use of terrain.
  4) "Introduction to Algorithms" by Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, and Clifford Stein is a comprehensive computer science textbook written in the late 20th century. The book follows a structured approach to teaching algorithms, covering a wide range of topics from basic data structures to advanced algorithmic techniques.
  5) "Vesper Talks to Girls" by Laura A. Knott is a collection of motivational addresses written in the early 20th century. The book compiles talks given to young women at Bradford Academy, addressing aspects of personal development, friendships, and the importance of character. 

  After you finished that first paragraph, please write a concise summary of the book in the second paragraph.
  Focus on the actualy content of the book (i.e. the characters, the content, the storyline etc.).
  Make sure to cover only the main points and main ideas, whilst avoiding any unnecessary information or repetition.
  Overall this summary should be relatively brief.

  In you writing use simple, clear, consise and expressive language.
  State the name of the book and the author's name only once throughout your response. Always write in English. And never include any urls in your response."""}
  prompt2 = {"role": "assistant", "content": "Understood! Please provide the book and I will follow your instructions."}
  prompt3 = {"role": "user", "content": "START OF BOOK: \n" + text + "\nEND OF BOOK"}

  response = openai_client.chat.completions.create(model="gpt-5", messages=[system_prompt, prompt1, prompt2, prompt3])
  response = response.choices[0].message.content
  return response

def format_result(result):
    summary = result.replace('*', '"')
    summary = summary.replace('_', '"')
    summary = summary.replace('"""', '"')
    summary = summary.replace('""', '"')
    # removing new lines because of gutenberg website can't display newlines in HTML (unfortunately)
    summary = summary.replace("\n", " ")
    # add sql requirement to escape single quotes with an additional single quote
    summary = summary.replace("'", "''")
    return summary


def summarise_book(book_content, title):
    chunk_size = 24000
    print("Summarising: ", title)
    if count_tokens(book_content) > chunk_size:
        beginning_of_book = get_first_chunk(book_content, chunk_size)
        summary = summarise_beginning_of_book(title, beginning_of_book)
    else:
        summary = summarise_entire_book(title, book_content)
    summary = format_result(summary)
    return summary


def save_summary(book_id, summary, file):
    beginning = "insert into attributes (fk_books,fk_attriblist,text,nonfiling) values (" + str(book_id) + ",520,'"
    note = " (This is an automatically generated summary.)"
    end = "',0);"
    sql = beginning + str(summary) + note + end

    with open(file, "a") as f:
        f.write(f"{sql}\n")