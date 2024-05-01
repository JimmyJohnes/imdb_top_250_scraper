import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/71.0.3578.98 Safari/537.36'
}

URL = "https://m.imdb.com/chart/top/"
MOVIES_DATA = []


def scrape_movie_data(movie_link):
    response = requests.get(url=movie_link, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.find('span', class_='hero__primary-text', attrs={'data-testid': 'hero__primary-text'}).text
    rating = soup.find('span', class_='sc-bde20123-1 cMEQkK').text

    genre_div = soup.find('div', {'class': 'ipc-chip-list__scroller'})
    genres = [chip.find('span', {'class': 'ipc-chip__text'}).get_text() for chip in genre_div.find_all('a')]

    year_div = soup.find('div', class_="sc-b7c53eda-0 dUpRPQ")
    year_link = year_div.find('a', class_="ipc-link ipc-link--baseAlt ipc-link--inherit-color")
    year = year_link.text

    director = soup.find('a', class_="ipc-metadata-list-item__list-content-item "
                                     "ipc-metadata-list-item__list-content-item--link").text

    cast_links = soup.find_all('a', {'data-testid': 'title-cast-item__actor'})
    cast = [link.get_text() for link in cast_links]

    first_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.ipc-lockup-overlay.ipc-focusable'))
    )

    first_link.click()

    link_for_img = driver.find_element(By.CSS_SELECTOR, 'a[data-testid="mv-gallery-button"]').get_attribute('href')

    second_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-testid="mv-gallery-button"]'))
    )

    second_link.click()

    response = requests.get(url=f'{link_for_img}', headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    img_src = soup.find('img', class_='poster').get('src')

    movie_data = {
        "title": title,
        "rating": rating,
        "genres": genres,
        "release_year": year,
        "director": director,
        "cast": cast,
        "image": img_src
    }

    return movie_data


chrome_options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    driver.get(URL)

    movies = driver.find_elements(By.CSS_SELECTOR, "a.ipc-title-link-wrapper h3.ipc-title__text")
    movie_links = [movie.find_element(By.XPATH, "./ancestor::a").get_attribute('href') for movie in movies]

    for link in movie_links[:251]:
        driver.get(link)
        # time.sleep(0.25)
        movie_data = scrape_movie_data(link)
        MOVIES_DATA.append(movie_data)
        # time.sleep(0.25)
        driver.back()

finally:

    df = pd.DataFrame(MOVIES_DATA)
    df.to_csv("imdb_top_250_movies_dataset.csv")

    driver.quit()
