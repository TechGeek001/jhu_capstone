import csv
import pathlib


class CSVLogger:
    def __init__(self, filename: str, fieldnames: list):
        self.filename = pathlib.Path(filename)
        self.fieldnames = fieldnames
        self.file_exists = self.filename.is_file()

        # Open the file in append mode and set up the CSV writer
        self.file = open(self.filename, mode="a", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)

        # Write the header if the file doesn't already exist
        if not self.file_exists:
            self.writer.writeheader()

    def log(self, data: dict):
        """Log a dictionary of key/value pairs to the CSV file.

        Parameters
        ----------
        data : dict
            The data to log to the CSV file.
        """
        self.writer.writerow(data)
        self.file.flush()

    def close(self):
        """Close the file when done."""
        self.file.close()
