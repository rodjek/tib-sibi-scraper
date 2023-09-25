import logging
import time
from sibi_scraper.book import Book
from sibi_scraper.book_list import BookList
from sibi_scraper.web import Session


class Scraper:
    """Scrape Indonesian text books from SIBI.

    Attributes
    ----------
    classes : obj:`list` of str
        The class numbers to scrape books for.
    book_list : obj:`sibi_scraper.book_list.BookList`
        The BookList storing the details of all previously scraped books.

    """
    CLASSES = ["all"] + [str(i) for i in range(1, 13)]
    api_host = "https://api.buku.kemdikbud.go.id"
    api_endpoint = f"{api_host}/api/catalogue/getPenggerakTextBooks"

    def __init__(self, class_, book_list_file):
        """Initialise a new Scraper.

        Parameters
        ----------
        class_ : obj:`list` of str
            A list of class numbers or "all" to scrape all classes.
        book_list_file : str
            The path to the book list CSV.

        """
        self.book_list = BookList(book_list_file)

        if "all" in class_:
            self.classes = self.CLASSES[1:]
        else:
            self.classes = class_

    def run(self):
        """Run the scraper.

        First, load the book list from the CSV file. Then iterate through the
        specified classes, querying the SIBI API for a list of books for each
        class, downloading any book returned that was not already in the book
        list. Finally, the updated book list is saved back to the CSV file.

        """
        self.book_list.load()

        for class_ in self.classes:
            found_books = self.search_for_books(class_)

            for book_json in found_books['results']:
                if not self.book_list.exists(book_json['title']):
                    logging.info("New book: %s", book_json['title'])
                    new_book = Book.from_api(book_json)
                    if new_book:
                        self.book_list.add(new_book)
                    time.sleep(10)

        self.book_list.save()

    def search_for_books(self, class_):
        """Query the SIBI API for the books for a given class.

        Parameters
        ----------
        class_ : str
            The class number, 1 to 12.

        Returns
        -------
        dict
            The parsed JSON result from the API if successful, otherwise an
            empty dict.

        """
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

        return {}
