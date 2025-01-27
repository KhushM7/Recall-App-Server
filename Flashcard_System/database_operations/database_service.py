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

# Configure logging
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DatabaseService:
    def __init__(self, db_path: str):
        """Initialize the database service with all its operations."""
        logger.info("Initializing DatabaseService with db_path: %s", db_path)

        if not isinstance(db_path, str) or not db_path.strip():
            logger.error("Invalid database path provided: %s", db_path)
            raise ValueError("Invalid database path provided.")

        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info("Database connection established successfully.")
        except sqlite3.Error as e:
            logger.error("Error connecting to the database at %s: %s", db_path, e)
            raise RuntimeError(f"Failed to connect to database: {e}")

        # Initialize operation classes
        try:
            self.flashcard_ops = FlashcardOperations(self.conn)
            self.user_performance_ops = UserPerformanceOperations(self.conn)
            self.user_settings_ops = UserSettingsOperations(self.conn)
            self.daily_review_log_ops = DailyReviewLogOperations(self.conn)
            logger.info("Operation classes initialized successfully.")
        except Exception as e:
            logger.error("Error initializing operation classes: %s", e)
            raise RuntimeError(f"Failed to initialize operation classes: {e}")

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            try:
                logger.info("Closing database connection.")
                self.conn.close()
                logger.info("Database connection closed successfully.")
            except sqlite3.Error as e:
                logger.error("Error closing the database connection: %s", e)
                raise RuntimeError(f"Failed to close the database connection: {e}")
        else:
            logger.warning(
                "Attempted to close a non-existent or already closed database connection."
            )
