class ScraperError(Exception):
    """Exception raised for errors during book scraping.

    Attributes
    ----------
    title : str
        The title of the book being scraped.
    message : str
        Explanation of the error

    """
    def __init__(self, title, message):
        self.title = title
        self.message = message
        super().__init__(self.message)
