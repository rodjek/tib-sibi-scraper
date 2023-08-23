import requests


class Session:
    _ua = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self._ua})

# session = requests.Session()
# session.headers.update({'User-Agent': ua})
# r = session.get(
#    'https://api.buku.kemdikbud.go.id/api/catalogue/getPenggerakTextBooks',
#    params: {'limit': 2000, 'type_pdf': '', 'level_paud': ''})
