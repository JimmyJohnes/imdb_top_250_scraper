import time
import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
#from selenium import webdriver
#from selenium.webdriver.common.by import By
#from selenium.webdriver.chrome.service import Service
#from webdriver_manager.chrome import ChromeDriverManager
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC

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
    """ returns if a given key is in the year format {\d\d\d\d}"""
    return bool(re.search(r'\d\d\d\d',key))

def get_top_250_movies_titles(soup)->list[str]:
    """ given the BeautifulSoup html object, returns all 250 titles of the listed movies"""
    titles = soup.find_all('h3', class_='ipc-title__text')
    titles = [item.text for item in titles if is_in_ordered_list(item.text)]
    return titles

def get_top_250_movies_ratings(soup)->list[str]:
    """ given the BeautifulSoup html object, returns all 250 ratings of the listed movies"""
    ratings = soup.find_all('span', class_='ipc-rating-star ipc-rating-star--base ipc-rating-star--imdb ratingGroup--imdb-rating')
    ratings = [item.text.replace("\xa0"," ") for item in ratings]
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


def scrape_movie_data(base_link, chart_link,headers):

    response = fetch(f"{base_link}{chart_link}",headers)
    soup = BeautifulSoup(response.text, 'lxml')

    titles = get_top_250_movies_titles(soup)

    ratings = get_top_250_movies_ratings(soup)

    years = get_top_250_movies_release_years(soup)

    links = get_top_250_movies_links(soup)

    genres = get_top_250_movies_genres(links,headers)

    
    #print([{
    #    "name": titles[index],
    #    "genre": genres[index]
    #    } for index in range(len(genres))])

#    genre_div = soup.find('div', {'class': 'ipc-chip-list__scroller'})
#    genres = [chip.find('span', {'class': 'ipc-chip__text'}).get_text() for chip in genre_div.find_all('a')]
#
#    year_div = soup.find('div', class_="sc-b7c53eda-0 dUpRPQ")
#    year_link = year_div.find('a', class_="ipc-link ipc-link--baseAlt ipc-link--inherit-color")
#    year = year_link.text
#
#    try:
#        directors_ul = soup.select_one('span:contains("Directors") + div ul').find_all('li')
#        directors = [director.text for director in directors_ul]
#    except:
#        directors = [soup.find('a', class_="ipc-metadata-list-item__list-content-item "
#                                           "ipc-metadata-list-item__list-content-item--link").text]
#
#    cast_links = soup.find_all('a', {'data-testid': 'title-cast-item__actor'})
#    cast = [actor.get_text() for actor in cast_links]
#
#    first_link = WebDriverWait(driver, 10).until(
#        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.ipc-lockup-overlay.ipc-focusable'))
#    )
#
#    first_link.click()
#
#    link_for_img = driver.find_element(By.CSS_SELECTOR, 'a[data-testid="mv-gallery-button"]').get_attribute('href')
#
#    second_link = WebDriverWait(driver, 10).until(
#        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-testid="mv-gallery-button"]'))
#    )
#
#    second_link.click()
#
#    response = requests.get(url=f'{link_for_img}', headers=HEADERS)
#    response.raise_for_status()
#
#    soup = BeautifulSoup(response.text, 'html.parser')
#    img_src = soup.find('img', class_='poster').get('src')
#
    movie_data = {
        "titles": titles,
        "ratings": ratings,
        "genres": genres,
        "release_years": years,
#        "director(s)": directors,
#        "cast": cast,
#        "image": img_src
    }
#
    return movie_data
#
#
#chrome_options = webdriver.ChromeOptions()
#driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
#
#try:
#    driver.get(URL)
#
#    movies = driver.find_elements(By.CSS_SELECTOR, "a.ipc-title-link-wrapper h3.ipc-title__text")
#    movie_links = [movie.find_element(By.XPATH, "./ancestor::a").get_attribute('href') for movie in movies]
#
#    for link in movie_links[:251]:
#        driver.get(link)
#        # time.sleep(0.25)
#
#        current_movie_data = scrape_movie_data(link)
#        MOVIES_DATA.append(current_movie_data)
#        # time.sleep(0.25)
#
#        driver.back()
#
#except Exception as e:
#    print(f'Error has occurred: {e}')
#
#finally:
#    df = pd.DataFrame(MOVIES_DATA)
#    df.to_csv("imdb_top_250_movies_dataset.csv")
#    driver.quit()
#
data = scrape_movie_data(BASE_URL,TOP_MOVIES_URL,HEADERS)
print(pd.DataFrame(data))
