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
                        default="all", dest="classes",
                        help="the level of books to scrape")
    parser.add_argument("--debug", action="store_true", dest="debug",
                        help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s",
                            level=logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    if os.path.isfile("book_list.csv"):
        migrate_book_list("book_list.csv", "sibi_book_list.csv")

    Scraper(args.classes, "sibi_book_list.csv").run()


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
