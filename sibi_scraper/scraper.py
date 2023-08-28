import logging
import time
from sibi_scraper.book import Book
from sibi_scraper.web import Session


class Scraper:
    CLASSES = ["all"] + [str(i) for i in range(1, 13)]
    api_host = "https://api.buku.kemdikbud.go.id"
    api_endpoint = f"{api_host}/api/catalogue/getPenggerakTextBooks"

    def __init__(self, classes, book_list_file):
        self.book_list_file = book_list_file

        if classes == "all":
            self.classes = self.CLASSES[1:]
        else:
            self.classes = [classes]

    def run(self):
        Book.load_book_list(self.book_list_file)

        for class_ in self.classes:
            found_books = self.search_for_books(class_)

            for r in found_books['results']:
                if not Book.exists(r['title']):
                    logging.info(f"New book {r['title']!r}")
                    Book.from_api(r)
                    time.sleep(10)

        Book.save_book_list(self.book_list_file)

    def search_for_books(self, class_):
        response = Session().session.get(
            self.api_endpoint,
            params={
                "limit": 2000,
                "type_pdf": "",
                f"class_{class_}": "",
            }
        )

        if response.ok:
            return response.json()
        else:
            return {}
