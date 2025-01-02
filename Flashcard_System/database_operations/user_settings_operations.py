from abc import ABC
from typing import Optional, Tuple, Dict, Any, List

import logging

from Flashcard_System.database_operations.base_database_operations import (
    BaseDatabaseOperations,
)


class UserSettingsOperations(BaseDatabaseOperations, ABC):
    def fetch(self, query: str, params: Tuple = ()) -> List[Any]:
        """Fetch multiple rows from the database."""
        try:
            return super().fetch(query, params)
        except Exception as e:
            logging.error(f"Error fetching data in UserSettingsOperations: {e}")
            raise

    def fetch_one(self, query: str, params: Tuple = ()) -> Dict[str, Any]:
        """Fetch a single row from the database."""
        try:
            return super().fetch_one(query, params)
        except Exception as e:
            logging.error(f"Error fetching one row in UserSettingsOperations: {e}")
            raise

    def insert(self, query: str, params: Tuple = ()) -> None:
        """Insert data into the database."""
        try:
            super().insert(query, params)
        except Exception as e:
            logging.error(f"Error inserting data in UserSettingsOperations: {e}")
            raise

    def update(self, query: str, params: Tuple = ()) -> None:
        """Update data in the database."""
        try:
            super().update(query, params)
        except Exception as e:
            logging.error(f"Error updating data in UserSettingsOperations: {e}")
            raise

    def delete(self, query: str, params: Tuple = ()) -> None:
        """Delete data from the database."""
        try:
            super().delete(query, params)
        except Exception as e:
            logging.error(f"Error deleting data in UserSettingsOperations: {e}")
            raise

    def fetch_daily_review_limit(self, user_id: int) -> Optional[int]:
        """Fetch the daily review limit for a user from UserSettings."""
        logging.info(f"Fetching daily review limit for user_id: {user_id}")

        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")

        try:
            query = """
                SELECT daily_review_limit 
                FROM UserSettings 
                WHERE user_id = ?
            """
            result = self.fetch_one(query, (user_id,))
            return result["daily_review_limit"] if result else None
        except Exception as e:
            logging.error(f"Error fetching daily review limit for user {user_id}: {e}")
            raise
