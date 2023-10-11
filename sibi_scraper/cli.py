import argparse
import csv
import datetime
import logging
from pathlib import Path

from sibi_scraper.scraper import Scraper


def main():
    parser = argparse.ArgumentParser(
        prog="sibi_scraper",
        description="Scrape books from SIBI for TIB.")
    parser.add_argument("-c", "--class", choices=Scraper.CLASSES,
                        dest="classes", nargs="+", type=str,
                        help="the class of text books to scrape")
    parser.add_argument("-n", "--nontext", choices=Scraper.NON_TEXT_LEVELS,
                        dest="non_text_levels", nargs="+", type=str,
                        help="the level of non-text books to scrape")
    parser.add_argument("--debug", action="store_true", dest="debug",
                        help="Enable debug logging")
    args = parser.parse_args()

    old_book_list = Path("book_list.csv")
    book_list = Path("sibi_book_list.csv")
    failure_list = Path("sibi_failures.csv")

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s",
                            level=logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    # Temp migrations
    if old_book_list.is_file():
        migrate_book_list(old_book_list, book_list)
    add_type_column(book_list)

    Scraper(args.classes, args.non_text_levels, book_list, failure_list).run()


def migrate_book_list(old_list, new_list):
    with (old_list.open(newline="", encoding="utf-8") as csv_input,
          new_list.open("w", newline="", encoding="utf-8") as csv_output):
        writer = csv.writer(csv_output)
        reader = csv.reader(csv_input)

        all_rows = []
        row = next(reader)
        row.append("Date Downloaded")
        row.append("Category")
        all_rows.append(row)

        for row in reader:
            path = Path("books") / row[1] / row[4]
            if not path.is_file():
                row.append("")
            else:
                file_ctime = path.stat().st_ctime
                downloaded_on = datetime.datetime.fromtimestamp(file_ctime)
                row.append(downloaded_on.strftime("%Y-%m-%d %H:%M:%S"))

            row.append("Curriculum Text")
            all_rows.append(row)

        writer.writerows(all_rows)

    old_list.unlink()


def add_type_column(book_list):
    new_file = Path(f"{book_list}.new")

    with book_list.open(newline="", encoding="utf-8") as csv_input:
        reader = csv.reader(csv_input)
        all_rows = []
        row = next(reader)

        if "Type" in row:
            return

        row.append("Type")
        all_rows.append(row)

        for row in reader:
            row.append("PDF")
            all_rows.append(row)

        with new_file.open("w", newline="", encoding="utf-8") as csv_output:
            writer = csv.writer(csv_output)
            writer.writerows(all_rows)

    new_file.rename(book_list)


if __name__ == "__main__":
    main()
