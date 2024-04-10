import csv
import logging

from sibi_scraper.book import Book


class BookList:
    """A collection of Books that have been scraped.

    Attributes
    ----------
    path : str
        The path to the CSV file where the book list is stored.
    books : obj:`list` of obj:`sibi_scraper.book.Book`
        The list of Books that have been scraped.

    """

    _csv_fields = [
        "Book List Title",
        "Class",
        "ISBN",
        "Edition",
        "File Name",
        "Pages",
        "English Title",
        "Date Downloaded",
        "Category",
        "Type",
        "Level",
    ]

    def __init__(self, path):
        """Initialise a new BookList.

        Parameters
        ----------
        path : str
            The path to the CSV file where the book list is stored.

        """
        self.path = path.resolve()
        self.books = []

    def load(self):
        """Load the data from the CSV file into the BookList."""
        if not self.path.is_file():
            return

        logging.debug("Loading %s", self.path)
        with self.path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                book = Book(
                    title=row["Book List Title"],
                    class_=row["Class"],
                    isbn=row["ISBN"],
                    edition=row["Edition"],
                    file=row["File Name"],
                    pages=row["Pages"],
                    english_title=row["English Title"],
                    date_downloaded=row["Date Downloaded"],
                    category=row["Category"],
                    type_=row["Type"],
                    level=row["Level"],
                )
                self.books.append(book)

    def save(self):
        """Save the BookList into the CSV file."""
        logging.debug("Saving %s", self.path)

        parent = self.path.parent
        if not parent.is_dir():
            parent.mkdir(parents=True)

        with self.path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self._csv_fields)
            writer.writeheader()
            for book in self.books:
                writer.writerow(self.book_to_csv(book))

    def book_to_csv(self, book):
        """Convert a Book into a format suitable for saving to the CSV file.

        Parameters
        ----------
        book : obj:`sibi_scraper.book.Book`
            The Book to be converted.

        Returns
        -------
        dict
            A dictionary representation of the given Book suitable for saving
            to the CSV file.

        """
        values = [
            book.title,
            book.class_,
            book.isbn,
            book.edition,
            book.file,
            book.pages,
            book.english_title,
            book.date_downloaded,
            book.category,
            book.type_,
            book.level,
        ]

        return dict(zip(self._csv_fields, values))

    def exists(self, book_title):
        """Check if there is a book with the given title in the list.

        Parameters
        ----------
        book_title : str
            The title of the book.

        Returns
        -------
        bool
            True if a book with the given title already exists in the book
            list, otherwise False.

        """
        return any(filter(lambda r: r.title == book_title, self.books))

    def add(self, new_book):
        """Add a Book to the book list.

        Parameters
        ----------
        new_book: obj:`sibi_scraper.book.Book`
            The book to be added to the book list.

        """
        self.books.append(new_book)

    def get(self, title):
        """Return a book from the book list.

        Parameters
        ----------
        title : str
            The title of the book to return.

        Returns
        -------
        obj:`sibi_scraper.book.Book`
            The named book.

        """

        return list(filter(lambda r: r.title == title, self.books))[0]
