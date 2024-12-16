# Updating code
from summaries import summarise_book, save_summary
from readability import calculate_readability, save_readability
from wiki_for_books import get_wikipedia_links, save_book_wikis
from categories import get_categories, save_categories
import time

# get and save readability results up to point
# get and save summary results up to point
# get and save category results up to point?

# to be done for levelling.
# summaries 74459 --> 74677
# readability 74459 --> 74677
# categories 74087 --> 74677
# nned summaries for categories ...


# last with category -- 74087
# last with summary -- 74459
# last with readability -- 74459
# last with wikipedia link -- 74677


from_id = 74087 # last one with it
to_id = 74677


with open("check_category_results.txt", "w") as f:
  test_set = open("categories_test.txt").read().split("\n")
  for query in test_set:
    try:
      book_id = query.split("values (")[1].split(",520")[0]
      summary = query.split("520,'")[1].split(" (This is an automatically")[0]   
      category_choice = get_categories(book_id, summary)
      category_ids = save_categories(book_id, category_choice)
      print(book_id)
      print(summary)
      print(category_choice)
      print(category_ids)
      print("---")
      f.write(f"{book_id}\n{summary}\n{category_choice}\n{category_ids}---\n")
    except Exception as e:
      print(e)
  


# for book_id in range(from_id+1, to_id+1):  
#   # print("Doing book: ", book_id)
#   # summary = summarise_book(book_id)
#   # print(summary)
#   # save_summary(book_id, summary)
#   # time.sleep(10)
  
#   # wiki_links = get_wikipedia_links(book_id)
#   # print("Results: ", wiki_links, "\n\n")
#   # save_book_wikis(book_id, wiki_links)
#   # time.sleep(10)
  
#   # readability = calculate_readability(book_id)
#   # print("Readability: ", readability)
#   # save_readability(book_id, readability)
#   # # time.sleep(10)

#   # ...
#   categories = get_categories(book_id, summary)
#   print("Categories: ", categories)
#   save_categories(book_id, categories)


  


# next -->
# get categories up to target level 74677
# --> make category choosing work well enough

# then see ...
# have them be uploaded
# do first real - supervised run - end of this month (or myb before?)
# ...

  








# run code monthly --> set up -- then first test end of this month ...
# ...
# ...

  

# get results up to same level --> 74677
# after that try to run joint code & joint provision of results ...


# categories code ... ((maybe categories dont need to be perfect --> big overhaul anyway after interface better ...))
# next --> sql query for categories

# --> formatting necessary to make sql queries right.
# add (This is autmatic summary) to end of summary for instance etc.

# later
# error handling?
# results all in one file?



                                            
  

# sql query for 

# new category code --> results good?
# (( myb nt super imp bcs overhaul entirely when new design ))

# questions:
# monthly, bi-weekly ...
# email-ok?

# saving of results ...

# specific faillures -- overlooked summary greg email
# --> alice in wonderland ...