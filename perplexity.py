import requests
import os
from dotenv import load_dotenv

load_dotenv()
perplexity_api = os.getenv("PERPLEXITY_API_KEY")


def life_dates_check(life_dates):
  "separate the different cases for life dates"
  try:
      life_dates = life_dates.split("-")
      if life_dates[0].isnumeric() and life_dates[1].isnumeric():
          return "complete"
      if life_dates[0].isnumeric():
          return "only_birth"
      if life_dates[1].isnumeric():
          return "only_death"
  except:
      return "complete"


def use_perplexity(prompt):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": """your job is to help me find the correct wikipedia link of a person I'm interested in. I will tell you what I know about that specific person. Then you'll search the web and try to find the right wikipedia link for that particular person if it exists. Make sure to only ever return ONE link to me if you find one for the person. Also make sure it's the wikipedia of the actual person him- or herself, not the wikipedia of the NAME per se or a disambiguation page or a list of some kind. Especially make sure it's NOT a wikipedia page that says that there is no wikipedia entry about that person! I am ONLY interested in the wikipedia entry that is centrally about that person and tells me something about him or her! So please only ever give me such a link if you can find it. If you can find one return only the wikipedia link. If you can not find it, return 'not found."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {perplexity_api}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(e)
        return "perplexity_error"


def perplexity_wiki_search(author_name, life_dates, titles):
  if life_dates:
    # record life dates
    # print("Life dates: ", life_dates)
  
    # do perplexity search
    if life_dates_check(life_dates) == "complete":
        prompt = f"""Find the wikipedia link of {author_name} who lived {life_dates} if it exists. Make sure the year of birth and year of death match exactly. Also make sure the name is an exact match (including middle names if any exist). However accept that first or middle names may be abbreviated. If you can find the correct link for this person, return ONLY the wikipedia link, nothing else! If you can not find a link for this perwson, return only the phrase 'not found.'. Please note that we're only interested in wikipedia entries that are either in English or in the native language of the author."""
    elif life_dates_check(life_dates) == "only_birth":
        life_dates = life_dates.split("-")[0]
        prompt = f"""Find the wikipedia link of {author_name} who was born in {life_dates} if it exists. Make sure the year of birth matches exactly. Also make sure the name is an exact match (including middle names if any exist). However accept that first or middle names may be abbreviated. If you can find the correct link for this person, return ONLY the wikipedia link, nothing else! If you can not find a link for this perwson, return only the phrase 'not found.'. Please note that we're only interested in wikipedia entries that are either in English or in the native language of the author."""
    elif life_dates_check(life_dates) == "only_death":
        life_dates = life_dates.split("-")[1]
        prompt = f"""Find the wikipedia link of {author_name} who died in {life_dates} if it exists. Make sure the year of death matches exactly. Also make sure the name is an exact match (including middle names if any exist). However accept that first or middle names may be abbreviated. If you can find the correct link for this person, return ONLY the wikipedia link, nothing else! If you can not find a link for this perwson, return only the phrase 'not found.'. Please note that we're only interested in wikipedia entries that are either in English or in the native language of the author."""
  else:
    print("No Life Dates.")
    if len(titles) == 1:
        # if only one titles on Gutenberg
        prompt = f"""I am trying to find the wikipedia link of "{author_name}" who wrote this book or script:
  - {titles[0]}
  
  Look for a wikipedia entry that has an exact name match with "{author_name}" (including middle names,if any exist) and that directly references the aforementioned work called "{titles[0]}" directly within its content.
  
  Accept that first or middle names of the author may be abbreviated.
  
  If you can find a wikipedia entry that fits these criteria, return ONLY that wikipedia link, nothing else! If you can not find it, return only the phrase 'not found.'. Please note that we're only interested in wikipedia entries that are either in English or in the native language of the author."""
    else:
        # if more than one title on Gutenberg
        titles = "\n-".join(titles)
        prompt = f"""I am trying to find the wikipedia link of "{author_name}" who wrote these books or scripts:
  - {titles}
  
  Look for a wikipedia entry that has an exact name match with "{author_name}" (including middle names if any exist) and that directly references at least one of the aforementioned works directly within its content.
  
  Accept that first or middle names of the author may be abbreviated.
  
  If you can find a wikipedia entry that fits these criteria, return ONLY that wikipedia link, nothing else! If you can not find it, return only the phrase 'not found.'. Please note that we're only interested in wikipedia entries that are either in English or in the native language of the author."""
  # print(prompt)
  perplexity_answer = use_perplexity(prompt)
  return perplexity_answer