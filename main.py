import time
import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/71.0.3578.98 Safari/537.36'
}

BASE_URL = "https://m.imdb.com"
TOP_MOVIES_URL = "/chart/top/"
MOVIES_DATA = []
MOVIE_TITLE = 2

def fetch(link: str = "", headers: dict[str,str] = {}):
    if link == "":
        raise Exception("Link cannot be empty")
    response = requests.get(url=link, headers=headers)
    return response


def is_in_ordered_list(key: str)->bool:
    """ returns if given key is in the top 250 list """
    return bool(re.search(r'^\d',key))

def is_a_year_format(key: str)->bool:
    """ returns if a given key is in the year format {\d \d \d \d}"""
    return bool(re.search(r'\d\d\d\d',key))

def get_top_250_movies_titles(soup)->list[str]:
    """ given the BeautifulSoup html object, returns all 250 titles of the listed movies"""
    titles = soup.find_all('h3', class_='ipc-title__text')
    titles = [item.text for item in titles if is_in_ordered_list(item.text)]
    return titles

def get_top_250_movies_ratings(soup)->list[str]:
    """ given the BeautifulSoup html object, returns all 250 ratings of the listed movies"""
    ratings = soup.find_all('span', class_='ipc-rating-star ipc-rating-star--base ipc-rating-star--imdb ratingGroup--imdb-rating')
    ratings = [item.text.replace("\xa0"," ").split(" ")[0] for item in ratings]
    return ratings 

def get_top_250_movies_release_years(soup)->list[str]:
    """ given the BeautifulSoup html object, returns the release years for the top 250 movies"""
    release_years = soup.find_all('span', class_='sc-b189961a-8 kLaxqf cli-title-metadata-item')
    release_years = [year.text for year in release_years if is_a_year_format(year.text)]
    return release_years

def get_top_250_movies_links(soup) -> list[str]:
    links = soup.find_all('a', class_="ipc-title-link-wrapper")
    links = [link["href"] for link in links if link["href"].split("/")[MOVIE_TITLE][0:2]=="tt"]
    return links

def get_top_250_movies_genres(links,headers):
    genres = []
    for link in links:
        title = str(link).split('/')[MOVIE_TITLE]
        sha256="8693f4655e3e7c5b6f786c6cf30e72dfa63a8fd52ebbad6f3a5ef7f03431c0f1"
        API_URL= "https://caching.graphql.imdb.com/?operationName=TMD_Storyline&variables={\"isAutoTranslationEnabled\":false,\"locale\":\"en-US\",\"titleId\":\""+title+"\"}&extensions={\"persistedQuery\":{\"sha256Hash\":\""+sha256+"\",\"version\":1}}"
        payload = {}
        headers = {
          'content-type': 'application/json'
        }
        response = requests.request("GET", API_URL, headers=headers, data=payload)

        data = response.json()
        data = [genre["text"] for genre in data["data"]["title"]["genres"]["genres"]]
        genres.append(','.join(data))
    return genres

def get_top_250_movies_images(soup) -> list[str]:
    images = soup.find_all('img', class_="ipc-image")
    for index in range(len(images)):
        images[index] = images[index]["src"]
    return images

def get_top_250_movies_directors(links, headers):
    """ given the top 250 movie links, returns a 2d list of all the directors of each movie """
    directors = []
    for link in links:
        title = str(link).split('/')[MOVIE_TITLE]
        response = requests.request("GET", f"https://m.imdb.com/title/{title}", headers=headers, data={})
        response.raise_for_status()
        soup = BeautifulSoup(response.text,"lxml")
        #
        # find the script tag that contains the word "Director"
        #
        check = re.compile("Director")
        soup = [s for s in soup.find_all('script') if re.search(check,s.text)]
        soup = BeautifulSoup(soup[0].text,"lxml")
        decoder = json.JSONDecoder()

        try:
            soup = decoder.decode(soup.text)
        except:
            soup = '{' + soup.text[soup.text.find("\"director\""):]
            soup = decoder.decode(soup)

        directors_for_this_movie = []
        if "props" in soup.keys():
            directors_for_this_movie = soup["props"]["pageProps"]["mainColumnData"]["directors"]
            directors_for_this_movie = [director_name["name"]["nameText"]["text"] for director_name in directors_for_this_movie[0]["credits"]]
        else:
            directors_for_this_movie = soup["director"]
            directors_for_this_movie = [director["name"] for director in directors_for_this_movie]
        directors.append(','.join(directors_for_this_movie))
    return directors

def get_top_250_movies_cast(links, headers):
    """ given the top 250 movie links, returns a 2d list of all the directors of each movie """
    cast = []
    for link in links:
        title = str(link).split('/')[MOVIE_TITLE]
        response = requests.request("GET", f"https://m.imdb.com/title/{title}", headers=headers, data={})
        response.raise_for_status()
        soup = BeautifulSoup(response.text,"lxml")
        #
        # find the script tag that contains the word "cast"
        #
        check = re.compile("cast")
        soup = [s for s in soup.find_all('script') if re.search(check,s.text)]
        soup = BeautifulSoup(soup[0].text,"lxml")
        decoder = json.JSONDecoder()

        try:
            soup = decoder.decode(soup.text)
        except:
            soup = '{' + soup.text[soup.text.find("\"actor\""):]
            soup = decoder.decode(soup)

        cast_for_this_movie = []
        if "props" in soup.keys():
            cast_for_this_movie = soup["props"]["pageProps"]["mainColumnData"]["cast"]
            cast_for_this_movie = [cast_name["node"]["name"]["nameText"]["text"] for cast_name in cast_for_this_movie["edges"]]
        else:
            cast_for_this_movie = soup["actor"]
            cast_for_this_movie= [cast["name"] for cast in cast_for_this_movie]
        cast.append(','.join(cast_for_this_movie))
    return cast

def scrape_movie_data(base_link, chart_link,headers):

    response = fetch(f"{base_link}{chart_link}",headers)
    soup = BeautifulSoup(response.text, 'lxml')

    titles = get_top_250_movies_titles(soup)

    ratings = get_top_250_movies_ratings(soup)

    years = get_top_250_movies_release_years(soup)

    links = get_top_250_movies_links(soup)

    genres = get_top_250_movies_genres(links,headers)

    images = get_top_250_movies_images(soup)
    images.pop()
    
    directors = get_top_250_movies_directors(links,headers)
    
    cast = get_top_250_movies_cast(links,headers)

    movie_data = {
        "titles": titles,
        "ratings": ratings,
        "genres": genres,
        "release_years": years,
        "director(s)": directors,
        "cast": cast,
        "image": images,
        "link": [base_link + link for link in links]
    }
    return movie_data

start = time.time()
print("Starting the Scrapin")
data = scrape_movie_data(BASE_URL,TOP_MOVIES_URL,HEADERS)
print("Scraping ended, time taken:",time.time() - start)
data = pd.DataFrame(data)
data.to_csv("data.csv")
