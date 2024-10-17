"""Module to manage logging for the application."""

import logging
import pathlib
import sys
from logging.handlers import RotatingFileHandler

from pythonjsonlogger import jsonlogger

from drone_ips.utils import Singleton


class LogManagerSingleton(metaclass=Singleton):
    """Singleton class to manage logging for the application."""

    LOGGER_NAME = "drone_ips"
    LOG_DIRECTORY = pathlib.Path("logs")
    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIRECTORY / f"{LOGGER_NAME}_log.json"

    def __init__(self):
        if not hasattr(self, "_initialized"):  # Check if already initialized
            self._initialized = True  # Mark the instance as initialized

            # Set up the parent logger
            self._parent_logger = logging.getLogger(LogManagerSingleton.LOGGER_NAME)
            self._parent_logger.setLevel(logging.DEBUG)
            self._parent_logger.propagate = False

            # File handler with JSON formatting
            file_handler = LogManagerSingleton._get_file_handler(LogManagerSingleton.LOG_FILE)
            self._parent_logger.addHandler(file_handler)

            # Console handler with custom formatting
            console_handler = LogManagerSingleton._get_console_handler()
            self._parent_logger.addHandler(console_handler)

            # Set up exception handling
            LogManagerSingleton._setup_exception_handling(self._parent_logger)
            self._parent_logger.info("Logger initialized")

    @property
    def parent_logger(self) -> logging.Logger:
        """Return the parent, or root, logger object that children are derived from.

        Returns
        -------
        logging.Logger
            The parent logger object.
        """
        return self._parent_logger

    def get_logger(self, logger_name: str) -> logging.Logger:
        """Return a child logger, derived from the parent logger.

        Parameters
        ----------
        logger_name : str
            The name of the child logger to create.

        Returns
        -------
        logging.Logger
            The child logger object.
        """
        full_name = f"{self.LOGGER_NAME}.{logger_name}"
        self.parent_logger.info(f"Creating logger: {full_name}")
        logger = logging.getLogger(full_name)
        return logger

    @staticmethod
    def _get_file_handler(log_file: pathlib.Path) -> RotatingFileHandler:
        """Create and return a rotating file handler with JSON formatting.

        Parameters
        ----------
        log_file : pathlib.Path
            The path to the log file to write to.

        Returns
        -------
        RotatingFileHandler
            The file handler object.
        """
        json_formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d"
        )
        file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
        file_handler.setFormatter(json_formatter)
        return file_handler

    @staticmethod
    def _get_console_handler() -> logging.StreamHandler:
        """Create and return a console handler with a custom formatter.

        Returns
        -------
        logging.StreamHandler
            The console handler object.
        """
        console_handler = logging.StreamHandler()
        console_formatter = CustomConsoleFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
        )
        console_handler.setFormatter(console_formatter)
        return console_handler

    @staticmethod
    def _setup_exception_handling(logger: logging.Logger):
        """Set up custom handling for unhandled exceptions.

        Parameters
        ----------
        logger : logging.Logger
            The logger to use for logging unhandled exceptions.
        """

        def handle_exception(exc_type, exc_value, exc_traceback):
            """Handle unhandled exceptions by logging them.

            Parameters
            ----------
            exc_type : type
                The type of the exception.
            exc_value : Exception
                The exception instance.
            exc_traceback : traceback
                The traceback object.
            """
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

        sys.excepthook = handle_exception


class CustomConsoleFormatter(logging.Formatter):
    """Custom formatter to handle line breaks for console output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the message of the log record in the console.

        Parameters
        ----------
        record : logging.LogRecord
            The log record to format.

        Returns
        -------
        str
            The formatted log message.
        """
        record.msg = record.msg.replace("\n", "\\n")
        result = super().format(record)
        result = result.replace("\\n", "\n")
        return result
