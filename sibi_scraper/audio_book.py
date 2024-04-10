# pylint: disable=too-many-arguments
import datetime
import logging
import time
import urllib.parse
from pathlib import Path

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from sibi_scraper.audio_book_list import AudioBookList
from sibi_scraper.book import Book
from sibi_scraper.errors import ScraperError
from sibi_scraper.failure_list import FailureList
from sibi_scraper.web import Session


class AudioBook(Book):
    def __init__(self, **kwargs):
        self.file_list = None
        self.failure_list = None

        super().__init__(**kwargs)

    @classmethod
    def from_api(cls, json_blob):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        params = {
            "title": json_blob["title"],
            "isbn": json_blob["isbn"],
            "edition": json_blob["edition"],
            "date_downloaded": now,
            "type_": "Audio",
            "file": json_blob["slug"],
            "level": json_blob["level"]
        }

        if json_blob.get("class", "") in ["", None]:
            params["class_"] = json_blob["level"]
        else:
            params["class_"] = json_blob["class"]

        new_book = cls(**params)

        new_book.set_category(json_blob["category"])
        new_book.english_title = new_book.translate(new_book.title)

        new_book.download_audio_files(json_blob["slug"])

        if not new_book.failure_list.isempty():
            return None

        return new_book

    def get_audiobook_details(self, slug):
        response = Session().session.get(
            "https://api.buku.kemdikbud.go.id/api/catalogue/getDetails",
            params={
                "slug": slug,
            },
        )

        if not response.ok:
            raise ScraperError(self.title,
                               "Failed to get book details: "
                               f"error {response.status_code}")

        return response.json()

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3),
           retry=retry_if_exception_type((
               httpx.ConnectError,
               httpx.ReadTimeout,
               TimeoutError)),
           reraise=True)
    def download_audio_files(self, slug):
        try:
            audiobook_details = self.get_audiobook_details(slug)
        except httpx.HTTPError as e:
            raise ScraperError(self.title, e.message) from e

        self.file = self.safe_path(slug)
        download_dir = Path("audiobooks") / self.class_ / self.file
        if not download_dir.is_dir():
            download_dir.mkdir(parents=True)

        self.file_list = AudioBookList(download_dir / "files.csv")
        self.failure_list = FailureList(download_dir / "failures.csv")
        self.file_list.load()
        self.failure_list.load()

        for attachment in audiobook_details["results"]["audio_attachment"]:
            if self.file_list.exists(attachment["title"]):
                continue

            filename = Path(
                urllib.parse.unquote(attachment["attachment"]),
            ).name
            download_path = download_dir / filename

            try:
                self.download_audio_file(
                    attachment["title"],
                    attachment["attachment"],
                    attachment["chapter"],
                    attachment["sub_chapter"],
                    download_path,
                )
                self.file_list.add(
                    attachment["title"],
                    self.translate(attachment["title"]),
                    attachment["chapter"],
                    attachment["sub_chapter"],
                    filename,
                )
                if self.failure_list.exists(attachment["title"]):
                    self.failure_list.remove(attachment["title"])
                time.sleep(10)
            except ScraperError as e:
                self.failure_list.add(e.title, e.message)
            except httpx.HTTPError as e:
                self.failure_list.add(self.title, e.message)

        self.failure_list.save()
        self.file_list.save()

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3),
           retry=retry_if_exception_type((
               httpx.ConnectError,
               httpx.ReadTimeout,
               TimeoutError)),
           reraise=True)
    def download_audio_file(self, title, attachment, chapter, sub_chapter,
                            path):
        ident = " - ".join([self.title, title, chapter, sub_chapter])
        logging.info("Downloading %s", ident)

        if attachment in ["", None]:
            raise ScraperError(ident, f"Blank URL: {ident}")

        response = Session().session.get(attachment)
        if not response.ok:
            logging.info("Unable to download %s: error %d",
                         attachment, response.status_code)
            raise ScraperError(ident, f"Unable to download {attachment}: "
                               f"error {response.status_code}")

        with path.open("wb") as local_file:
            local_file.write(response.content)
