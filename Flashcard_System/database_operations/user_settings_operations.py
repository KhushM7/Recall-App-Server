import logging
from abc import ABC
from typing import Optional, Tuple, Dict, Any, List

from Flashcard_System.database_operations.base_database_operations import (
    BaseDatabaseOperations,
)

# Configure logging
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class UserSettingsOperations(BaseDatabaseOperations, ABC):
    def fetch(self, query: str, params: Tuple = ()) -> List[Any]:
        """Fetch multiple rows from the database."""
        try:
            return super().fetch(query, params)
        except Exception as e:
            logger.error("Error fetching data in UserSettingsOperations: %s", e)
            raise

    def fetch_one(self, query: str, params: Tuple = ()) -> Dict[str, Any]:
        """Fetch a single row from the database."""
        try:
            return super().fetch_one(query, params)
        except Exception as e:
            logger.error("Error fetching one row in UserSettingsOperations: %s", e)
            raise

    def insert(self, query: str, params: Tuple = ()) -> None:
        """Insert data into the database."""
        try:
            super().insert(query, params)
        except Exception as e:
            logger.error("Error inserting data in UserSettingsOperations: %s", e)
            raise

    def update(self, query: str, params: Tuple = ()) -> None:
        """Update data in the database."""
        try:
            super().update(query, params)
        except Exception as e:
            logger.error("Error updating data in UserSettingsOperations: %s", e)
            raise

    def delete(self, query: str, params: Tuple = ()) -> None:
        """Delete data from the database."""
        try:
            super().delete(query, params)
        except Exception as e:
            logger.error("Error deleting data in UserSettingsOperations: %s", e)
            raise

    def fetch_daily_review_limit(self, user_id: int) -> Optional[int]:
        """Fetch the daily review limit for a user from UserSettings."""
        logger.info("Fetching daily review limit for user_id: %d", user_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        try:
            query = """
                SELECT daily_review_limit 
                FROM UserSettings 
                WHERE user_id = ?
            """
            result = self.fetch_one(query, (user_id,))
            if result:
                logger.info(
                    "Daily review limit for user_id %d fetched successfully.", user_id
                )
            else:
                logger.info("No daily review limit found for user_id %d.", user_id)
            return result["daily_review_limit"] if result else None
        except Exception as e:
            logger.error(
                "Error fetching daily review limit for user %d: %s", user_id, e
            )
            raise

    def update_daily_review_limit(self, user_id: int, new_limit: int) -> None:
        """Update the daily review limit for a user."""
        logger.info(
            "Updating daily review limit for user_id: %d to %d", user_id, new_limit
        )

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")
        if not isinstance(new_limit, int) or new_limit <= 0:
            logger.error("Invalid new_limit provided: %d", new_limit)
            raise ValueError(f"Invalid new_limit: {new_limit}")

        try:
            query = """
                UPDATE UserSettings
                SET daily_review_limit = ?
                WHERE user_id = ?
            """
            self.insert(query, (new_limit, user_id))
            logger.info(
                "Daily review limit for user_id %d updated successfully.", user_id
            )
        except Exception as e:
            logger.error(
                "Error updating daily review limit for user %d: %s", user_id, e
            )
            raise
