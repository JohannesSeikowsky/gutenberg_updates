import json
import logging

from sqlalchemy import select, and_

from libgutenberg.Models import Book, Attribute
from libgutenberg import GutenbergDatabase

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

OB = GutenbergDatabase.Objectbase(False)
session = OB.get_session()

def load_jsonl(filename):
    with open(filename, "r") as data_jsons:
        for line in data_jsons:
            datum = json.loads(line)
            yield datum

# load from summaries file from Johannes
fn = "summaries_10_25.jsonl"
count = 0
for datum in load_jsonl(fn):
    for pg_id in datum:
        sum = datum[pg_id]
        book = session.query(Book).where(Book.pk == pg_id).first()
        break
    if not book:
        logger.error(f'book number {pg_id} does not exist')
        continue
    if book.categories != []: # don't want summaries for non-texts
        logger.warning(f'book number {pg_id} is not text')
        continue
    for attrib in session.query(Attribute).where(and_(
            Attribute.fk_attriblist == 520,
            Attribute.fk_books == pg_id)):
        # already has a summary
        if "(This is an automatically generated summary.)" in attrib.text:
            # go ahead and replace the automated summary)
            logger.warning(f'replacing automated summary on {pg_id}')
            attrib.text = sum
            break
    else:
        # no existing 520s, add the new
        book.attributes.append(Attribute(fk_attriblist=520, nonfiling=0, text=sum))
        logger.warning(f'added summary to {pg_id}')
    count += 1
logger.info(f'added {count} summaries')
session.commit()

# remove summaries for non-text things
disclaimer = '%%automatically generated summary%%'
for pg_id in [76962,50,65,127,576,4656,10802,11220]:
    for attrib in session.query(Attribute).where(and_(Attribute.fk_attriblist == 520,
                                                      Attribute.fk_books == pg_id,
                                                      Attribute.text.like(disclaimer))):
        session.delete(attrib)
        logger.info(f'{attrib.pk}  deleted')
session.commit()

#remove summaries with signs of AI punting
for bad_sign in ['It appears%%', 'It seems%%', '%%no content provided%%', '%%no content has been provided%%']:
    num_bad = 0
    for attrib in session.query(Attribute).where(and_(Attribute.fk_attriblist == 520,
                                                      Attribute.text.like(bad_sign))):
        session.delete(attrib)
        num_bad += 1
    logger.info(f'{num_bad} removed for {bad_sign}')
session.commit()