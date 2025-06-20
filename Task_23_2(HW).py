import requests
from bs4 import BeautifulSoup
import time
from dataclasses import dataclass, asdict
from typing import List, Optional
import re
import warnings
import json
import csv
import pandas as pd
from datetime import datetime


@dataclass
class Film:
    title: str  # Название фильма
    release_date: str  # Дата выхода
    rating: str  # Рейтинг
    genres: str  # Жанры
    url: str  # Ссылка на фильм


class TMDBParser:
    def __init__(self):
        self.base_url = 'https://www.themoviedb.org'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        self.delay = 2
        self.timeout = 15
        self.month_map = {
            'января': '01', 'февраля': '02', 'марта': '03',
            'апреля': '04', 'мая': '05', 'июня': '06',
            'июля': '07', 'августа': '08', 'сентября': '09',
            'октября': '10', 'ноября': '11', 'декабря': '12'
        }
        warnings.filterwarnings("ignore", category=FutureWarning, module="soupsieve")

    def _get_page(self, url: str) -> Optional[str]:
        try:
            time.sleep(self.delay)
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            return None

    def _parse_date(self, date_str: str) -> str:
        try:
            if not date_str:
                return "Дата не указана"
            return date_str.strip()
        except Exception as e:
            print(f"Ошибка парсинга даты: {e}")
            return "Ошибка даты"

    def _parse_film_card(self, card) -> Optional[Film]:
        try:
            content = card.find('div', class_='content')
            if not content:
                return None

            title = content.find('a').get_text(strip=True)
            date_elem = content.find('p')
            release_date = self._parse_date(date_elem.get_text()) if date_elem else "Дата не указана"

            rating_elem = card.find('div', class_='user_score_chart')
            rating = rating_elem['data-percent'] if rating_elem and 'data-percent' in rating_elem.attrs else 'N/A'

            url_elem = card.find('a', href=True)
            url = f"{self.base_url}{url_elem['href']}" if url_elem else ''

            genres = self._get_film_genres(url) if url else 'Не указаны'

            return Film(
                title=title,
                release_date=release_date,
                rating=f"{rating}%",
                genres=genres,
                url=url
            )
        except Exception as e:
            print(f"Ошибка карточки: {e}")
            return None

    def _get_film_genres(self, url: str) -> str:
        html = self._get_page(url)
        if not html:
            return 'Не указаны'

        soup = BeautifulSoup(html, 'html.parser')
        genres = []
        genre_elems = soup.select('span.genres a, a.genre')
        for elem in genre_elems:
            genre = elem.get_text(strip=True)
            if genre and genre not in genres:
                genres.append(genre)

        return ', '.join(genres) if genres else 'Не указаны'

    def get_top_films(self, count: int = 10) -> List[Film]:
        films = []
        page = 1

        while len(films) < count and page <= 5:
            url = f"{self.base_url}/movie?language=ru&page={page}"
            html = self._get_page(url)
            if not html:
                break

            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.find_all('div', class_='card style_1')
            if not cards:
                break

            for card in cards:
                film = self._parse_film_card(card)
                if film:
                    films.append(film)
                    if len(films) >= count:
                        break

            page += 1

        return films[:count]

    def export_to_json(self, films: List[Film], filename: str = "films.json"):
        """Сохранение в JSON файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([asdict(film) for film in films], f, ensure_ascii=False, indent=2)
        print(f"Dati esportati in {filename}")

    def export_to_csv(self, films: List[Film], filename: str = "films.csv"):
        """Сохранение в CSV файл"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(films[0]).keys())
            writer.writeheader()
            writer.writerows([asdict(film) for film in films])
        print(f"Dati esportati in {filename}")

    def export_to_excel(self, films: List[Film], filename: str = "films.xlsx"):
        """Сохранение в Excel файл"""
        df = pd.DataFrame([asdict(film) for film in films])
        df.to_excel(filename, index=False)
        print(f"Dati esportati in {filename}")


if __name__ == "__main__":
    print("TMDB Парсер - Топ фильмов\n")
    parser = TMDBParser()

    try:
        start_time = time.time()
        films = parser.get_top_films(10)

        for i, film in enumerate(films, 1):
            print(f"{i}. {film.title} | Дата: {film.release_date} | ★ {film.rating}")
            print(f"   Жанры: {film.genres}")
            print(f"   Ссылка: {film.url}\n")

        # Сохранение во всех форматах
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parser.export_to_json(films, f"films_{timestamp}.json")
        parser.export_to_csv(films, f"films_{timestamp}.csv")
        parser.export_to_excel(films, f"films_{timestamp}.xlsx")

        print("Экспорт успешно завершен")  # Сообщение об успешном экспорте
    except Exception as e:
        print(f"Произошла ошибка при экспорте: {e}")  # Сообщение об ошибке