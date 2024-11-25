"""A simple CSV logger that logs data to a CSV file."""

import csv
import pathlib
from io import TextIOWrapper
from typing import Optional, Union

from drone_ips.logging import LogManager


class CSVLogger:
    """A simple CSV logger that logs data to a CSV file.

    Parameters
    ----------
    filename : str
        The name of the CSV file to log data to.
    fieldnames : list
        A list of fieldnames to use in the CSV file.
    """

    def __init__(self, filename: Optional[str] = None, fieldnames: Optional[list] = None):
        self.logger = LogManager.get_logger("csv_logger")
        self._fh: Optional[TextIOWrapper] = None
        if filename is not None:
            self.open(filename, fieldnames)

    @property
    def file_open(self) -> bool:
        """Check if the log file is open.

        Returns
        -------
        bool
            True if the log file is open, False otherwise.
        """
        return self._fh is not None and not self._fh.closed

    def log(self, data: dict):
        """Log a dictionary of key/value pairs to the CSV file.

        Parameters
        ----------
        data : dict
            The data to log to the CSV file.
        """
        if not self.file_open:
            raise RuntimeError("The log file is not open.")
        assert self._fh is not None  # for mypy

        new_fields = [key for key in data.keys() if key not in self._fieldnames]

        # If new fields are discovered, recreate the log file with updated fieldnames
        if new_fields:
            self._update_fieldnames(new_fields)

        # Ensure all fieldnames are in the data, filling missing fields with empty strings
        row = {field: data.get(field, "") for field in self._fieldnames}
        self._writer.writerow(row)
        self._fh.flush()

    def open(self, filename: Union[str, pathlib.Path], fieldnames: Optional[list] = None):
        """Close the current log file and start a new one with a given filename.

        Parameters
        ----------
        filename : str
            The name of the new CSV file to log data to.
        fieldnames : list, optional
            A list of fieldnames to use in the CSV file.
        """
        # Close the current log file if one exists
        self.close()

        # Set the new filename and check if the file exists
        self._fieldnames = self._sort_fieldnames(fieldnames)
        # Set the filename as a pathlib.Path object
        if isinstance(filename, str):
            self._filename = pathlib.Path(filename)
        # Open the new file in write mode and set up the CSV writer
        self._fh = open(self._filename, mode="w", newline="", encoding="utf-8")
        self.logger.info(f"Opened log file: {self._filename}")
        # Create a new writer
        self._writer = csv.DictWriter(self._fh, fieldnames=self._fieldnames)
        # Write the header row
        self._writer.writeheader()

    def close(self):
        """Close the file when done."""
        if self.file_open:
            assert isinstance(self._fh, TextIOWrapper)  # for mypy
            self._fh.close()
            self.logger.info(f"Closed log file: {self._filename}")
            self._fh = None

    def _sort_fieldnames(self, fieldnames: Optional[list] = None) -> list:
        """Sort the fieldnames in alphabetical order, after the key.

        Parameters
        ----------
        fieldnames : list, optional
            A list of fieldnames to sort.

        Returns
        -------
        list
            The sorted list of fieldnames, preserving the key at index 0.
        """
        if fieldnames is None or len(fieldnames) == 0:
            return []
        sorted_fieldnames = fieldnames[:]
        if len(sorted_fieldnames) > 2:
            sorted_fieldnames = [sorted_fieldnames[0]] + sorted(sorted_fieldnames[1:])
        return sorted_fieldnames

    def _update_fieldnames(self, new_fields: list):
        """Update the CSV file with new fieldnames and retain the existing data.

        Parameters
        ----------
        new_fields : list
            A list of new fields to add to the CSV file.
        """

        self.logger.info(f"Got new fields: {', '.join(new_fields)}")
        # Update fieldnames by appending new fields to the original fieldnames
        updated_fieldnames = self._fieldnames + new_fields

        # Read the existing data
        with open(self._filename, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, fieldnames=self._fieldnames)
            rows = list(reader)
        # Skip the header row
        if len(rows) > 0:
            for k, v in rows[0].items():
                # In the header row, the key and value are the same
                # If any values are different, this isn't a duplicate header
                if k != v:
                    break
            else:
                if len(rows) > 1:
                    rows = rows[1:]
                else:
                    rows = []

        # Re-open the file using the new fields
        self.open(self._filename, updated_fieldnames)

        # Write back the old data with the new fieldnames (fill missing fields with empty strings)
        for row in rows:
            updated_row = {field: row.get(field, "") for field in updated_fieldnames}
            self._writer.writerow(updated_row)
