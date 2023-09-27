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
    non_text_levels : obj:`list` of str
        The levels to scrape non-text books for.

    """
    CLASSES = ["all"] + [str(i) for i in range(1, 13)]
    NON_TEXT_LEVELS = ["all", "A", "B1", "B2", "B3", "C", "D", "E", "transisi"]
    api_host = "https://api.buku.kemdikbud.go.id"
    categories = {
        "curriculum": f"{api_host}/api/catalogue/getPenggerakTextBooks",
        "text": f"{api_host}/api/catalogue/getTextBooks",
        "non_text": f"{api_host}/api/catalogue/getNonTextBooks",
    }

    def __init__(self, text_classes, non_text_levels, book_list_file):
        """Initialise a new Scraper.

        Parameters
        ----------
        text_classes : obj:`list` of str
            A list of class numbers or "all" to scrape all classes.
        book_list_file : str
            The path to the book list CSV.
        non_text_levels : obj:`list` of str
            A list of levels or "all" to scrape all levels of non-text books.

        """
        self.book_list = BookList(book_list_file)
        self.classes = []
        self.non_text_levels = []

        if text_classes is None and non_text_levels is None:
            self.classes = self.CLASSES[1:]
            self.non_text_levels = self.NON_TEXT_LEVELS[1:]

        if text_classes is not None:
            if "all" in text_classes:
                self.classes = self.CLASSES[1:]
            else:
                self.classes = text_classes

        if non_text_levels is not None:
            if "all" in non_text_levels:
                self.non_text_levels = self.NON_TEXT_LEVELS[1:]
            else:
                self.non_text_levels = non_text_levels

    def run(self):
        """Run the scraper.

        First, load the book list from the CSV file. Then iterate through the
        specified classes, querying the SIBI API for a list of books for each
        class, downloading any book returned that was not already in the book
        list. Finally, the updated book list is saved back to the CSV file.

        """
        self.book_list.load()

        for class_ in self.classes:
            for category in self.categories.keys():
                found_books = self.search_for_books(class_, category)

                for book_json in found_books['results']:
                    if not self.book_list.exists(book_json['title']):
                        logging.info("New book: %s", book_json['title'])
                        new_book = Book.from_api(book_json)
                        if new_book:
                            self.book_list.add(new_book)
                        time.sleep(10)

        for level in self.non_text_levels:
            found_books = self.search_for_non_text_books(level)

            for book_json in found_books['results']:
                if not self.book_list.exists(book_json['title']):
                    logging.info("New book: %s", book_json['title'])
                    new_book = Book.from_api(book_json)
                    if new_book:
                        self.book_list.add(new_book)
                    time.sleep(10)

        self.book_list.save()

    def search_for_books(self, class_, category):
        """Query the SIBI API for the text books for a given class.

        Parameters
        ----------
        class_ : str
            The class number, 1 to 12.
        category : str
            The category of text books to scrape, "curriculum" or "text".

        Returns
        -------
        dict
            The parsed JSON result from the API if successful, otherwise an
            empty dict.

        """
        response = Session().session.get(
            self.categories[category],
            params={
                "limit": 2000,
                "type_pdf": "",
                f"class_{class_}": "",
            }
        )

        if response.ok:
            return response.json()

        return {}

    def search_for_non_text_books(self, level):
        """Query the SIBI API for the non-text books for a given level.

        Parameters
        ----------
        level : str
            The level of non-text book: A, B1, B2, B3, C, D, E, transisi.

        Returns
        -------
        dict
            The parsed JSON result from the API if successful, otherwise an
            empty dict.

        """
        response = Session().session.get(
            self.categories["non_text"],
            params={
                "limit": 2000,
                "type_pdf": "",
                f"level_{level}": "",
            }
        )

        if response.ok:
            return response.json()

        return {}
