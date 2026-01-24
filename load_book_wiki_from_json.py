import json
import logging
import csv
import re

from sqlalchemy import select, and_

from libgutenberg.Models import Attribute, Book
from libgutenberg import GutenbergDatabase

OB = GutenbergDatabase.Objectbase(False)
session = OB.get_session()
logger = logging.getLogger()

def load_jsonl(filename):
    with open(filename, "r") as data_jsons:
        for line in data_jsons:
            datum = json.loads(line)
            yield datum

re_wiki = re.compile(r'(..)\.wikipedia.org')
CAPTION = 'Wikipedia page about this book'

def which_wiki(text):
    try:
        return re_wiki.search(text).group(1)
    except:
        return ''

fn = "book_wikipedia_10_25.jsonl"
count = 0

#clean up bare wiki 500s


for datum in load_jsonl(fn):
    for pg_id in datum.keys():
        urls = datum[pg_id].split()
        break

    book = session.query(Book).where(Book.pk == pg_id).first()

    if not book:
        logger.error(f'book number {pg_id} does not exist')
        continue

    for url in urls:
        marctext = f'Wikipedia page about this book: {url}'
        ww = which_wiki(url)

        for attrib in session.query(Attribute).where(and_(
                Attribute.fk_attriblist == 500,
                Attribute.fk_books == pg_id,
            )):
            # already has wikilink(s)
            att_ww = which_wiki(attrib.text)
            if attrib.text.startswith(CAPTION) and att_ww == ww:
                # same wiki for book, replace
                logger.warning(f'replacing wiki link  on {pg_id}')
                attrib.text = marctext
                break
        else:
            # no matching attributes
            book.attributes.append(Attribute(fk_attriblist=500, nonfiling=len(CAPTION), text=marctext))
            logger.warning(f'added wiki to {pg_id}')
            
    count += 1
    
logger.info(f'added {count} author urls')
session.commit()