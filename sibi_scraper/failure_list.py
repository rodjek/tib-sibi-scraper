import csv
import os


class FailureList:
    _csv_fields = [
        'Title',
        'Failure',
    ]

    def __init__(self, path):
        self.path = path
        self.failures = {}

    def load(self):
        if not os.path.isfile(self.path):
            return

        with open(self.path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.failures[row['Title']] = row['Failure']

    def save(self):
        with open(self.path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self._csv_fields)
            writer.writeheader()
            for title in self.failures:
                row = dict(zip(self._csv_fields,
                               [title, self.failures[title]]))
                writer.writerow(row)

    def add(self, key, value):
        self.failures[key] = value

    def remove(self, key):
        del self.failures[key]

    def exists(self, key):
        return key in self.failures
