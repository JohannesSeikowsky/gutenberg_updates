import json
import logging
import csv

from sqlalchemy import select, and_

from libgutenberg.Models import  Author, AuthorUrl
from libgutenberg import GutenbergDatabase

OB = GutenbergDatabase.Objectbase(False)
session = OB.get_session()
logger = logging.getLogger()

def load_jsonl(filename):
    with open(filename, "r") as data_jsons:
        for line in data_jsons:
            datum = json.loads(line)
            yield datum

fn = "author_wikipedia_10_25.jsonl"
count = 0
for datum in load_jsonl(fn):
    for auth_id in datum.keys():
        [description, url] = datum[auth_id].split(',')
        break

    author = session.query(Author).where(Author.id == auth_id).first()
    if not author:
        logger.error(f'author number {auth_id} does not exist')
        continue

    for webpage in author.webpages:
        # note fix description for 4774 and 58055
        if webpage.description == description:
            # already has a link
            webpage.url = url
            break
    else:
        webpage = AuthorUrl(fk_authors=author.id, description=description, url=url)
            
    count += 1
    
logger.info(f'added {count} author urls')
session.commit()