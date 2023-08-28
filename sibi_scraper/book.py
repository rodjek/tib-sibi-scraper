# pylint: disable=too-many-arguments
import csv
import googletrans
import os
import urllib.parse
import logging
import httpx
from PyPDF2 import PdfReader
from sibi_scraper.web import Session


class Book:
    """
    A book that has been scraped from SIBI.
    """

    book_list = []
    _csv_fields = [
        'Book List Title',
        'Class',
        'ISBN',
        'Edition',
        'File Name',
        'Pages',
        'English Title',
    ]

    def __init__(self, title=None, class_=None, isbn=None, edition=None,
                 file=None, english_title=None, pages=None, append=True):
        """
        Initialise a Book from known values.
        """

        self.title = title
        self.english_title = english_title
        self.class_ = class_
        self.isbn = isbn
        self.edition = edition
        self.file = file
        self.pages = pages

        if not self.english_title:
            self.translate_title()

        if append:
            self.book_list.append(self)

    @classmethod
    def from_api(cls, json_blob):
        """
        Initialise a Book from the result of a SIBI API query and download it.
        """
        new_book = cls(
            title=json_blob['title'],
            class_=json_blob['class'],
            isbn=json_blob['isbn'],
            edition=json_blob['edition'],
            file=json_blob['attachment'],
            append=False,
        )

        try:
            if new_book.download_file():
                cls.book_list.append(new_book)
        except httpx.ReadTimeout:
            logging.warning(f"Timed out downloading {json_blob['attachment']}")

        return new_book

    @classmethod
    def load_book_list(cls, path):
        if not os.path.isfile(path):
            return

        with open(path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                cls(
                    title=row['Book List Title'],
                    class_=row['Class'],
                    isbn=row['ISBN'],
                    edition=row['Edition'],
                    file=row['File Name'],
                    pages=row['Pages'],
                    english_title=row['English Title'],
                )

    @classmethod
    def save_book_list(cls, path):
        with open(path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=cls._csv_fields)
            writer.writeheader()
            for book in cls.book_list:
                writer.writerow(book.to_csv())

    @classmethod
    def exists(cls, book_title):
        return any(filter(lambda r: r.title == book_title, cls.book_list))

    def translate_title(self):
        translator = googletrans.Translator()
        self.english_title = translator.translate(
            self.title, src='id', dest='en').text

    def __repr__(self):
        class_name = type(self).__name__
        return f"{class_name}(title={self.title!r})"

    def to_csv(self):
        values = [
            self.title,
            self.class_,
            self.isbn,
            self.edition,
            self.file,
            self.pages,
            self.english_title,
        ]

        return dict(zip(self._csv_fields, values))

    def download_file(self):
        filename = os.path.basename(urllib.parse.unquote(self.file))
        local_path = os.path.join("books", self.class_, filename)
        download_dir = os.path.dirname(local_path)

        if not os.path.isdir(download_dir):
            os.makedirs(download_dir)

        response = Session().session.get(self.file)
        if response.ok:
            with open(local_path, "wb") as local_file:
                local_file.write(response.content)
            self.file = filename
            self.pages = self.get_book_length(local_path)
            return True
        else:
            print(f"Unable to download {self.file}")
            return False

    def get_book_length(self, path):
        reader = PdfReader(path)
        return len(reader.pages)
