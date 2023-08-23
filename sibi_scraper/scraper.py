import logging
import time
from sibi_scraper.book import Book
from sibi_scraper.web import Session


class Scraper:
    LEVELS = ["all", "paud", "sd", "smp", "sma"]
    api_host = "https://api.buku.kemdikbud.go.id"
    api_endpoint = f"{api_host}/api/catalogue/getPenggerakTextBooks"

    def __init__(self, level, book_list_file):
        self.book_list_file = book_list_file

        if level == "all":
            self.level = self.LEVELS[1:]
        else:
            self.level = [level]

    def run(self):
        Book.load_book_list(self.book_list_file)

        for i in self.level:
            found_books = self.search_for_books(i)

            for r in found_books['results']:
                if not Book.exists(r['title']):
                    logging.info(f"New book {r['title']!r}")
                    Book.from_api(r, i)
                    time.sleep(10)

        Book.save_book_list(self.book_list_file)

    def search_for_books(self, level):
        response = Session().session.get(
            self.api_endpoint,
            params={
                "limit": 2000,
                "type_pdf": "",
                f"level_{level}": "",
            }
        )

        if response.ok:
            return response.json()
        else:
            return {}
