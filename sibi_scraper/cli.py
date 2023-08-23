import argparse
import logging
from sibi_scraper.scraper import Scraper


def main():
    parser = argparse.ArgumentParser(
        prog="sibi_scraper",
        description="Scrape books from SIBI for TIB.")
    parser.add_argument("-l", "--level", choices=Scraper.LEVELS, default="all",
                        dest="level", help="the level of books to scrape")
    parser.add_argument("--debug", action="store_true", dest="debug",
                        help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s",
                            level=logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    Scraper(args.level, "book_list.csv").run()


if __name__ == "__main__":
    main()
