import sqlite3
import logging

from Flashcard_System.database_operations.daily_review_log_operations import (
    DailyReviewLogOperations,
)
from Flashcard_System.database_operations.flashcard_operations import (
    FlashcardOperations,
)
from Flashcard_System.database_operations.user_performance_operations import (
    UserPerformanceOperations,
)
from Flashcard_System.database_operations.user_settings_operations import (
    UserSettingsOperations,
)


class DatabaseService:

    def __init__(self, db_path: str):
        """Initialize the database service with all its operations."""
        logging.info(f"Initializing DatabaseService with db_path: {db_path}")

        if not isinstance(db_path, str) or not db_path.strip():
            raise ValueError("Invalid database path provided.")

        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            logging.error(f"Error connecting to the database at {db_path}: {e}")
            raise RuntimeError(f"Failed to connect to database: {e}")

        # Initialize operation classes
        try:
            self.flashcard_ops = FlashcardOperations(self.conn)
            self.user_performance_ops = UserPerformanceOperations(self.conn)
            self.user_settings_ops = UserSettingsOperations(self.conn)
            self.daily_review_log_ops = DailyReviewLogOperations(self.conn)
        except Exception as e:
            logging.error(f"Error initializing operation classes: {e}")
            raise RuntimeError(f"Failed to initialize operation classes: {e}")

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            try:
                logging.info("Closing database connection")
                self.conn.close()
            except sqlite3.Error as e:
                logging.error(f"Error closing the database connection: {e}")
                raise RuntimeError(f"Failed to close the database connection: {e}")
        else:
            logging.warning(
                "Attempted to close a non-existent or already closed database connection."
            )
