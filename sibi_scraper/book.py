# pylint: disable=too-many-arguments
import datetime
import urllib.parse
from pathlib import Path

import googletrans
import httpx
import PyPDF2
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from sibi_scraper.errors import ScraperError
from sibi_scraper.web import Session


class Book:
    """A book that has been scraped from SIBI.

    Attributes
    ----------
    category : str
        The type of book (e.g. Textbook).
    class_ : str
        The school class that the book is for.
    date_downloaded : str
        A human readable date and time when the book was downloaded.
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
    type_ : str
        The type of book (PDF or Audio).

    """

    def __init__(self, title=None, class_=None, isbn=None, edition=None,
                 file=None, english_title=None, pages=None,
                 date_downloaded=None, category=None, type_=None):
        """Initialise a Book from known values.

        Parameters
        ----------
        category : str
            The type of book (e.g. Textbook).
        class_ : str
            The school class that the book is for.
        date_downloaded : str
            A human readable date and time when the book was downloaded.
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
        type_ : str
            The type of book (PDF or Audio).

        """

        self.title = title
        self.english_title = english_title
        self.class_ = class_
        self.isbn = isbn
        self.edition = edition
        self.file = file
        self.pages = pages
        self.date_downloaded = date_downloaded
        self.category = category
        self.type_ = type_

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
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        params = {
            "title": json_blob["title"],
            "isbn": json_blob["isbn"],
            "edition": json_blob["edition"],
            "file": json_blob["attachment"],
            "date_downloaded": now,
            "type_": "PDF",
        }

        if json_blob.get("class", "") in ["", None]:
            params["class_"] = json_blob["level"]
        else:
            params["class_"] = json_blob["class"]

        new_book = cls(**params)

        new_book.set_category(json_blob["category"])
        new_book.english_title = new_book.translate(new_book.title)

        try:
            if new_book.download_file():
                return new_book
        except httpx.ReadTimeout as e:
            raise ScraperError(params["title"],
                               f"Timed out downloading {params['file']}",
                               ) from e
        return None

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3),
           retry=retry_if_exception_type((
               httpx.ConnectError,
               httpx.ReadTimeout)),
           reraise=True)
    def translate(self, text):
        """Translate the given text to English using Google Translate."""
        translator = googletrans.Translator()
        return translator.translate(text, src="id", dest="en").text

    def set_category(self, category):
        """Translate the Book category from the API response.

        Parameters
        ----------
        category : str
            The category string as returned by the API: buku_sekolah_penggerak,
            buku_teks, buku_non_teks.

        Returns
        -------
        str
            Returns the translated category or "Unknown" if the category could
            not be translated.

        """
        categories = {
            "buku_sekolah_penggerak": "Curriculum Text",
            "buku_teks": "Text",
            "buku_non_teks": "Non-text",
        }

        self.category = categories.get(category, "Unknown")

    def __repr__(self):
        class_name = type(self).__name__
        return f"{class_name}(title={self.title!r})"

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3),
           retry=retry_if_exception_type((
               httpx.ConnectError,
               httpx.ReadTimeout)),
           reraise=True)
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
        if self.file in ["", None]:
            raise ScraperError(self.title, f"Blank URL: {self.title}")

        filename = Path(urllib.parse.unquote(self.file)).name
        local_path = Path("books") / self.class_ / filename
        download_dir = local_path.parent

        if not download_dir.is_dir:
            download_dir.mkdir(parents=True)

        response = Session().session.get(self.file)

        if not response.ok:
            raise ScraperError(self.title,
                               f"Unable to download {self.file}: "
                               f"error {response.status_code}")

        with local_path.open("wb") as local_file:
            local_file.write(response.content)

        try:
            self.pages = self.get_book_length(local_path)
        except PyPDF2.errors.PdfReadError as e:
            raise ScraperError(self.title, f"Corrupt PDF: {self.file}") from e

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
