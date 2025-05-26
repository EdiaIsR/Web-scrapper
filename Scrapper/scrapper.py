import requests
import csv
import os
from bs4 import BeautifulSoup

BASE_URL = "https://www.senscritique.com"
MAIN_PAGE_URL = "/liste/Bon_Films/66436?page="

FILMS_CSV_PATH = './films.csv'
STATS_CSV_PATH = './films_stats.csv'

STATS = {
    "FILMS_PER_REALISATEUR": {},
    "FILMS_PER_TYPE": {},
    "FILMS_PER_YEAR": {},
    "FILMS_PER_ACTOR": {},
    "BEST_ACTOR": "",
    "AVERAGE_DURATION": 0,
}

FILMS = []
DURATIONS = []

session = requests.session()

def main():
    delete_csv()
    for i in range(1, 11):
        try:
            print(f"Scrapping page {i}. Please wait...")
            main_page_content = session.get(f"{BASE_URL}{MAIN_PAGE_URL}{i}").content
            main_page_soup = BeautifulSoup(main_page_content, "html.parser")
            movies_links = get_movies_links(main_page_soup)
            print(f"Found {len(movies_links)} movies on this page.")
            scrap_movies_pages(movies_links)
            update_best_actor()
        except requests.RequestException as e:
            print(f"Error: {e}")
    create_csv()

def scrap_movies_pages(movies_links):
    for link in movies_links:
        infos = {}
        movie_page_content = session.get(f"{BASE_URL}{link}").content
        movie_page_soup = BeautifulSoup(movie_page_content, "html.parser")

        infos["title"] = movie_page_soup.find("h1").text
        print(f"Scrapping movie {infos['title']}. Please wait...")

        infos["realisateur"] = movie_page_soup.select_one("a.Text__SCText-sc-1aoldkr-0.Link__PrimaryLink-sc-1v081j9-0.eWSucP.bGxijB span").text
        infos["main_actors"] = [actor.find("a").text for actor in movie_page_soup.select("div.ContactCard__Container-sc-3teq8m-0.iCigEv div.ContactCard__Name-sc-3teq8m-1.FRNZA")]
        infos["main_type"] = movie_page_soup.select_one("a.Text__SCText-sc-1aoldkr-0.Link__PrimaryLink-sc-1v081j9-0.gATBvI.bGxijB").text
        infos["duration"], infos["release_date"] = get_movie_details(movie_page_soup)

        FILMS.append(infos)
        update_stats(infos)

def get_movies_links(soup):
    return [movie.find("a")["href"] for movie in soup.find_all("h3")]

def get_movie_details(soup):
    duration = release_date = ""
    details = soup.select_one("p.Text__SCText-sc-1aoldkr-0.Creators__Text-sc-1ghc3q0-0.gATBvI.LJhsB").text.split(" · ")
    for detail in details:
        if is_a_duration(detail):
            duration = detail
        elif is_a_date(detail):
            release_date = detail

    return duration, release_date

def update_stats(infos):
    STATS["FILMS_PER_REALISATEUR"].setdefault(infos["realisateur"], 0)
    STATS["FILMS_PER_REALISATEUR"][infos["realisateur"]] += 1

    STATS["FILMS_PER_TYPE"].setdefault(infos["main_type"], 0)
    STATS["FILMS_PER_TYPE"][infos["main_type"]] += 1

    year = infos["release_date"].split(" ")[2] if is_a_date(infos["release_date"]) else infos["release_date"].split(" ")[0]
    STATS["FILMS_PER_YEAR"].setdefault(year, 0)
    STATS["FILMS_PER_YEAR"][year] += 1

    for actor in infos["main_actors"]:
        STATS["FILMS_PER_ACTOR"].setdefault(actor, 0)
        STATS["FILMS_PER_ACTOR"][actor] += 1

    if infos["duration"]:
        DURATIONS.append(get_duration_in_minutes(infos["duration"]))
        STATS["AVERAGE_DURATION"] = sum(DURATIONS) / len(DURATIONS)

def update_best_actor():
    best_actor = max(STATS["FILMS_PER_ACTOR"], key=STATS["FILMS_PER_ACTOR"].get, default="")
    STATS["BEST_ACTOR"] = best_actor

def get_duration_in_minutes(duration):
    if is_a_duration(duration) and "h" in duration:
        try:
            hours = int(duration.split("h")[0])
            minutes = int(duration.split("h")[1].split("min")[0]) if "min" in duration else 0
            return hours * 60 + minutes
        except ValueError:
            return 0
    else:
        return 0

def is_a_duration(text):
    return any(x in text for x in ["h", "min"])

def is_a_date(text):
    months = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    return any(month in text for month in months)

def create_csv():
    create_films_csv()
    create_film_per_year_csv()
    create_film_per_realisateur_csv()
    create_film_per_type_csv()
    create_main_stats_csv()

def create_films_csv():
    with open(FILMS_CSV_PATH, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Titre', 'Réalisateur', 'Acteurs', 'Type', 'Durée', 'Date de sortie']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')

        writer.writeheader()
        for film in FILMS:
            writer.writerow({'Titre': film["title"], 'Réalisateur': film["realisateur"], 'Acteurs': ", ".join(film["main_actors"]), 'Type': film["main_type"], 'Durée': film["duration"], 'Date de sortie': film["release_date"]})

def create_film_per_year_csv():
    with open(STATS_CSV_PATH, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Année', 'Nombre de films']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')

        writer.writeheader()
        for annee, count in STATS["FILMS_PER_YEAR"].items():
            writer.writerow({'Année': annee, 'Nombre de films': count})

def create_film_per_realisateur_csv():
    with open('./films_stats.csv', 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Réalisateurs', 'Nombre de films']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')

        writer.writeheader()
        for realisateur, count in STATS["FILMS_PER_REALISATEUR"].items():
            writer.writerow({'Réalisateurs': realisateur, 'Nombre de films': count})

def create_film_per_type_csv():
    with open('./films_stats.csv', 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Type', 'Nombre de films']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')

        writer.writeheader()
        for type, count in STATS["FILMS_PER_TYPE"].items():
            writer.writerow({'Type': type, 'Nombre de films': count})

def create_main_stats_csv():
    with open('./films_stats.csv', 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Acteur le plus présent', 'Durée moyenne des films']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')

        writer.writeheader()
        writer.writerow({'Acteur le plus présent': STATS["BEST_ACTOR"], 'Durée moyenne des films': STATS["AVERAGE_DURATION"]})

def delete_csv():
    if os.path.exists("./films_stats.csv"):
        os.remove("./films_stats.csv")

if __name__ == "__main__":
    main()