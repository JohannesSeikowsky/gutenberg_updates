#add caption to bare wikipedia urls; split multiple wikipedia urls into separate attributes.

from libgutenberg import GutenbergDatabase

from libgutenberg.Models import Attribute
#clean up bare wiki 500s
CAPTION = 'Wikipedia page about this book:'
OB = GutenbergDatabase.Objectbase(False)
session = OB.get_session()
count = 0
for attrib in session.query(Attribute).where(
        Attribute.fk_attriblist == 500
    ).filter(Attribute.text.like('https://%%')):
    # 500 attr with bare url (or multiple bare urls) only bare urls are wikipedia urls)
    print(attrib.text)
    for url in attrib.text.split():
        newatt = Attribute(fk_books=attrib.fk_books, fk_attriblist=500, text=f'{CAPTION} {url}', nonfiling=len(CAPTION))
        session.add(newatt)
        count += 1
    session.delete(attrib)
print (count)
session.commit()