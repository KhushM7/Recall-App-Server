import logging
from abc import ABC
from typing import Tuple, Dict, Any, List

from Flashcard_System.database_operations.base_database_operations import (
    BaseDatabaseOperations,
)


class DailyReviewLogOperations(BaseDatabaseOperations, ABC):
    def fetch(self, query: str, params: Tuple = ()) -> List[Any]:
        """Fetch multiple rows from the database."""
        try:
            return super().fetch(query, params)
        except Exception as e:
            logging.error(f"Error fetching data in DailyReviewLogOperations: {e}")
            raise

    def fetch_one(self, query: str, params: Tuple = ()) -> Dict[str, Any]:
        """Fetch a single row from the database."""
        try:
            return super().fetch_one(query, params)
        except Exception as e:
            logging.error(f"Error fetching one row in DailyReviewLogOperations: {e}")
            raise

    def insert(self, query: str, params: Tuple = ()) -> None:
        """Insert data into the database."""
        try:
            super().insert(query, params)
        except Exception as e:
            logging.error(f"Error inserting data in DailyReviewLogOperations: {e}")
            raise

    def update(self, query: str, params: Tuple = ()) -> None:
        """Update data in the database."""
        try:
            super().update(query, params)
        except Exception as e:
            logging.error(f"Error updating data in DailyReviewLogOperations: {e}")
            raise

    def delete(self, query: str, params: Tuple = ()) -> None:
        """Delete data from the database."""
        try:
            super().delete(query, params)
        except Exception as e:
            logging.error(f"Error deleting data in DailyReviewLogOperations: {e}")
            raise

    def fetch_reviewed_today(self, user_id: int, review_date: str) -> int:
        """Fetch how many cards the user has already reviewed today."""
        logging.info(
            f"Fetching reviewed cards count for user_id: {user_id}, review_date: {review_date}"
        )

        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")
        if not isinstance(review_date, str):
            raise ValueError(f"Invalid review_date: {review_date}")

        try:
            query = """
                SELECT reviewed_cards_count 
                FROM DailyReviewLog 
                WHERE user_id = ? AND review_date = ?
            """
            result = self.fetch_one(query, (user_id, review_date))
            return result["reviewed_cards_count"] if result else 0
        except Exception as e:
            logging.error(
                f"Error fetching reviewed cards count for user {user_id} on {review_date}: {e}"
            )
            raise

    def increment_reviewed_card_count(self, user_id: int, review_date: str) -> None:
        """Increment the count of reviewed cards for the user in the DailyReviewLog."""
        logging.info(
            f"Incrementing reviewed card count for user_id: {user_id}, review_date: {review_date}"
        )

        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")
        if not isinstance(review_date, str):
            raise ValueError(f"Invalid review_date: {review_date}")

        try:
            query = """
                INSERT INTO DailyReviewLog (user_id, review_date, reviewed_cards_count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, review_date)
                DO UPDATE SET reviewed_cards_count = reviewed_cards_count + 1;
            """
            self.insert(query, (user_id, review_date))
        except Exception as e:
            logging.error(
                f"Error incrementing reviewed card count for user {user_id} on {review_date}: {e}"
            )
            raise
