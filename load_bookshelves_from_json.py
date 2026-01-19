import json
import logging

from sqlalchemy import select, and_

from libgutenberg.Models import  Book, Bookshelf
from libgutenberg import GutenbergDatabase

OB = GutenbergDatabase.Objectbase(False)
session = OB.get_session()
logger = logging.getLogger()

def load_jsonl(filename):
    with open(filename, "r") as data_jsons:
        for line in data_jsons:
            datum = json.loads(line)
            yield datum

fn = "categories_10_25.jsonl"
count = 0
for datum in load_jsonl(fn):
    for pg_id in datum.keys():
        bookshelf_id = datum[pg_id]
        book = session.query(Book).where(Book.pk == pg_id).first()
        break

    if not book:
        logger.error(f'book number {pg_id} does not exist')
        continue

    if book.categories != []: # don't want subjects for non-texts
        logger.warning(f'book number {pg_id} is not text')
        continue

    bookshelf = session.query(Bookshelf).where(Bookshelf.id == bookshelf_id).first()
    if not bookshelf:
        logger.error(f'Bookshelf number {bookshelf_id} does not exist')
        continue
    if not bookshelf.bookshelf.startswith('Category:'):
        logger.error(f'Bookshelf number {bookshelf_id} is not a browsing bookshelf')
        continue
        
    if bookshelf not in book.bookshelves:
        book.bookshelves.append(bookshelf)
    count += 1

    
logger.info(f'added {count} bookshelf assignments')  
session.commit()