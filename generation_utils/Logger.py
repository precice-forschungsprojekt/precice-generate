from pathlib import Path
from termcolor import colored
from datetime import datetime

class Logger:
    def __init__(self) -> None:
        """ Custom logger"""
        self.root_generated = Path(__file__).parent
        self._errors = []
        self._warnings = []
        self._messages = []

    def _log(self, msg: str, level: str, color: str, symbol: str) -> None:
        """
        Internal method to log a message with a specified level, color, and symbol.
        :param msg: The log message.
        :param level: The log level (e.g., INFO, SUCCESS, ERROR).
        :param color: The color for terminal output.
        :param symbol: Symbol to display alongside the log.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"{timestamp} {symbol} [{level}] {msg}"
        self._messages.append(formatted_msg)


    def print_all(self) -> None:
        """Prints all logged messages and clears the log state."""
        for message in self._messages:
            print(message)
        self._messages.clear()
    
    def clear_messages(self) -> None:
        """Clears all logged messages."""
        self._messages.clear()

    def success(self, msg: str) -> None:
        """Logs a success message."""
        self._log(msg, "SUCCESS", "green", "✅")

    def info(self, msg: str) -> None:
        """Logs an informational message."""
        self._log(msg, "INFO", "blue", "ℹ️")

    def warning(self, msg: str) -> None:
        """Logs a warning message."""
        self._log(msg, "WARNING", "yellow", "⚠️")
        self._warnings.append(msg)

    def error(self, msg: str) -> None:
        """Logs an error message."""
        self._log(msg, "ERROR", "red", "❌")
        self._errors.append(msg)

    def has_errors(self) -> bool:
        """Check if any errors have been logged."""
        return len(self._errors) > 0

    def has_warnings(self) -> bool:
        """Check if any warnings have been logged."""
        return len(self._warnings) > 0

    def get_warnings(self) -> list:
        """Retrieve logged warnings."""
        return self._warnings

    def clear_log_state(self) -> None:
        """Clear all logged errors and warnings."""
        self._errors.clear()
        self._warnings.clear()
