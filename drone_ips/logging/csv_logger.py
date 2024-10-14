"""A simple CSV logger that logs data to a CSV file."""

import csv
import pathlib


class CSVLogger:
    """A simple CSV logger that logs data to a CSV file.

    Parameters
    ----------
    filename : str
        The name of the CSV file to log data to.
    fieldnames : list
        A list of fieldnames to use in the CSV file.
    """

    def __init__(self, filename: str, fieldnames: list):
        self._filename = pathlib.Path(filename)
        self._fieldnames = fieldnames
        self._file_exists = self._filename.is_file()

        # Open the file in append mode and set up the CSV writer
        self._file = open(self._filename, mode="a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self._fieldnames)

        # Write the header if the file doesn't already exist
        if not self._file_exists:
            self._writer.writeheader()

    def log(self, data: dict):
        """Log a dictionary of key/value pairs to the CSV file.

        Parameters
        ----------
        data : dict
            The data to log to the CSV file.
        """
        new_fields = [key for key in data.keys() if key not in self._fieldnames]

        # If new fields are discovered, recreate the log file with updated fieldnames
        if new_fields:
            self._update_fieldnames(new_fields)

        # Ensure all fieldnames are in the data, filling missing fields with empty strings
        row = {field: data.get(field, "") for field in self._fieldnames}
        self._writer.writerow(row)
        self._file.flush()

    def _update_fieldnames(self, new_fields: list):
        """Update the CSV file with new fieldnames and retain the existing data.

        Parameters
        ----------
        new_fields : list
            A list of new fields to add to the CSV file.
        """
        # Update fieldnames by appending new fields to the original fieldnames
        updated_fieldnames = self._fieldnames + new_fields

        # Read the existing data
        self._file.close()
        with open(self._filename, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, fieldnames=self._fieldnames)
            rows = list(reader)

        # Write updated data with the new fieldnames
        self._file = open(self._filename, mode="w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=updated_fieldnames)
        self._writer.writeheader()

        # Write back the old data with the new fieldnames (fill missing fields with empty strings)
        for row in rows:
            updated_row = {field: row.get(field, "") for field in updated_fieldnames}
            self._writer.writerow(updated_row)

        # Update the fieldnames and the writer to use the updated fieldnames
        self._fieldnames = updated_fieldnames

    def close(self):
        """Close the file when done."""
        self._file.close()
