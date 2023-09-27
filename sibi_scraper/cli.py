import argparse
import csv
import datetime
import logging
import os
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

    old_book_list = "book_list.csv"
    book_list = "sibi_book_list.csv"
    failure_list = "sibi_failures.csv"

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s",
                            level=logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    if os.path.isfile(old_book_list):
        migrate_book_list(old_book_list, book_list)

    Scraper(args.classes, args.non_text_levels, book_list, failure_list).run()


def migrate_book_list(old_list, new_list):
    with (open(old_list, newline='', encoding='utf-8') as csv_input,
          open(new_list, 'w', newline='', encoding='utf-8') as csv_output):
        writer = csv.writer(csv_output)
        reader = csv.reader(csv_input)

        all_rows = []
        row = next(reader)
        row.append('Date Downloaded')
        row.append('Category')
        all_rows.append(row)

        for row in reader:
            path = os.path.join('books', row[1], row[4])
            if not os.path.isfile(path):
                row.append('')

            file_stat = os.stat(path)
            downloaded_on = datetime.datetime.fromtimestamp(file_stat.st_ctime)
            row.append(downloaded_on.strftime('%Y-%m-%d %H:%M:%S'))

            row.append('Curriculum Text')
            all_rows.append(row)

        writer.writerows(all_rows)

    os.remove(old_list)


if __name__ == "__main__":
    main()
