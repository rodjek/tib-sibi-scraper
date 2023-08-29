# pylint: disable=too-many-arguments
import logging
import os
import urllib.parse
import googletrans
import httpx
import PyPDF2
from sibi_scraper.web import Session


class Book:
    """A book that has been scraped from SIBI.

    Attributes
    ----------
    class_ : str
        The school class that the book is for.
    edition : str
        The edition of the book.
    english_title : str
        The title of the book, translated into English.
    file : str
        The filename of the downloaded book.
    isbn : str
        The ISBN of the book (if published).
    pages : str
        The number of pages in the book.
    title : str
        The title of the book.

    """

    def __init__(self, title=None, class_=None, isbn=None, edition=None,
                 file=None, english_title=None, pages=None):
        """Initialise a Book from known values.

        Parameters
        ----------
        class_ : str
            The school class that the book is for.
        edition : str
            The edition of the book.
        english_title : str
            The title of the book, translated into English.
        file : str
            The filename of the downloaded book.
        isbn : str
            The ISBN of the book (if published).
        pages : str
            The number of pages in the book.
        title : str
            The title of the book.

        """

        self.title = title
        self.english_title = english_title
        self.class_ = class_
        self.isbn = isbn
        self.edition = edition
        self.file = file
        self.pages = pages

    @classmethod
    def from_api(cls, json_blob):
        """
        Initialise a Book from the result of a SIBI API query.

        After initialisation the title is translated into English, the book PDF
        is downloaded, and the number of pages in the PDF is counted.

        Parameters
        ----------
        json_blob : dict
            A dictionary of values representing a Book as returned by an API
            call from SIBI.

        Returns
        -------
        obj:`sibi_scraper.book.Book` or None
            Returns the initialised Book object if the download was successful,
            otherwise None.

        """
        new_book = cls(
            title=json_blob['title'],
            class_=json_blob['class'],
            isbn=json_blob['isbn'],
            edition=json_blob['edition'],
            file=json_blob['attachment'],
        )

        new_book.translate_title()

        try:
            if new_book.download_file():
                return new_book
        except httpx.ReadTimeout:
            logging.warning("Timed out downloading %s",
                            json_blob['attachment'])
        return None

    def translate_title(self):
        """Translate the title to English using Google Translate."""
        translator = googletrans.Translator()
        self.english_title = translator.translate(
            self.title, src='id', dest='en').text

    def __repr__(self):
        class_name = type(self).__name__
        return f"{class_name}(title={self.title!r})"

    def download_file(self):
        """Download the book PDF.

        The PDF will be downloaded to a folder relative to the current working
        directory as follows:
            {CWD}/books/{class_}/{filename}

        Returns
        -------
        bool
            True if the file was downloaded and opened successfully, otherwise
            False.

        """
        filename = os.path.basename(urllib.parse.unquote(self.file))
        local_path = os.path.join("books", self.class_, filename)
        download_dir = os.path.dirname(local_path)

        if not os.path.isdir(download_dir):
            os.makedirs(download_dir)

        response = Session().session.get(self.file)

        if not response.ok:
            logging.warning("Unable to download: %s", self.file)
            return False

        with open(local_path, "wb") as local_file:
            local_file.write(response.content)

        try:
            self.pages = self.get_book_length(local_path)
        except PyPDF2.errors.PdfReadError:
            logging.warning("Corrupt PDF: %s", self.file)
            return False

        self.file = filename
        return True

    def get_book_length(self, path):
        """Read a PDF to determine the number of pages.

        Parameters
        ----------
        path : str
            The path to the PDF.

        Returns
        -------
        int
            The number of pages in the PDF.

        """
        reader = PyPDF2.PdfReader(path)
        return len(reader.pages)
