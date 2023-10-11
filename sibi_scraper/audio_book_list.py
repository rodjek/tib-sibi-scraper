import csv


class AudioBookList:
    _csv_fields = [
        "Title",
        "English Title",
        "Chapter",
        "Subchapter",
        "File Name",
    ]

    def __init__(self, path):
        self.path = path
        self.files = []

    def load(self):
        if not self.path.is_file():
            return

        with self.path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.files.append(row)

    def save(self):
        with self.path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self._csv_fields)
            writer.writeheader()
            for file in self.files:
                writer.writerow(file)

    def exists(self, title):
        return any(filter(lambda r: r["Title"] == title, self.files))

    def add(self, *params):
        data = dict(zip(self._csv_fields, params))
        self.files.append(data)
