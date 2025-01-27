import logging
from abc import ABC
from typing import Tuple, Dict, Any, List

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


class DailyReviewLogOperations(BaseDatabaseOperations, ABC):
    def fetch(self, query: str, params: Tuple = ()) -> List[Any]:
        """Fetch multiple rows from the database."""
        try:
            return super().fetch(query, params)
        except Exception as e:
            logger.error("Error fetching data in DailyReviewLogOperations: %s", e)
            raise

    def fetch_one(self, query: str, params: Tuple = ()) -> Dict[str, Any]:
        """Fetch a single row from the database."""
        try:
            return super().fetch_one(query, params)
        except Exception as e:
            logger.error("Error fetching one row in DailyReviewLogOperations: %s", e)
            raise

    def insert(self, query: str, params: Tuple = ()) -> None:
        """Insert data into the database."""
        try:
            super().insert(query, params)
        except Exception as e:
            logger.error("Error inserting data in DailyReviewLogOperations: %s", e)
            raise

    def update(self, query: str, params: Tuple = ()) -> None:
        """Update data in the database."""
        try:
            super().update(query, params)
        except Exception as e:
            logger.error("Error updating data in DailyReviewLogOperations: %s", e)
            raise

    def delete(self, query: str, params: Tuple = ()) -> None:
        """Delete data from the database."""
        try:
            super().delete(query, params)
        except Exception as e:
            logger.error("Error deleting data in DailyReviewLogOperations: %s", e)
            raise

    def fetch_reviewed_today(self, user_id: int, review_date: str) -> int:
        """Fetch how many cards the user has already reviewed today."""
        logger.info(
            "Fetching reviewed cards count for user_id: %d, review_date: %s",
            user_id,
            review_date,
        )

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")
        if not isinstance(review_date, str):
            logger.error("Invalid review_date provided: %s", review_date)
            raise ValueError(f"Invalid review_date: {review_date}")

        try:
            query = """
                SELECT reviewed_cards_count 
                FROM DailyReviewLog 
                WHERE user_id = ? AND review_date = ?
            """
            result = self.fetch_one(query, (user_id, review_date))
            reviewed_count = result["reviewed_cards_count"] if result else 0
            logger.info(
                "Fetched reviewed cards count for user_id: %d on %s: %d",
                user_id,
                review_date,
                reviewed_count,
            )
            return reviewed_count
        except Exception as e:
            logger.error(
                "Error fetching reviewed cards count for user_id %d on %s: %s",
                user_id,
                review_date,
                e,
            )
            raise

    def increment_reviewed_card_count(self, user_id: int, review_date: str) -> None:
        """Increment the count of reviewed cards for the user in the DailyReviewLog."""
        logger.info(
            "Incrementing reviewed card count for user_id: %d, review_date: %s",
            user_id,
            review_date,
        )

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")
        if not isinstance(review_date, str):
            logger.error("Invalid review_date provided: %s", review_date)
            raise ValueError(f"Invalid review_date: {review_date}")

        try:
            query = """
                INSERT INTO DailyReviewLog (user_id, review_date, reviewed_cards_count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, review_date)
                DO UPDATE SET reviewed_cards_count = reviewed_cards_count + 1;
            """
            self.insert(query, (user_id, review_date))
            logger.info(
                "Successfully incremented reviewed card count for user_id: %d on %s",
                user_id,
                review_date,
            )
        except Exception as e:
            logger.error(
                "Error incrementing reviewed card count for user_id %d on %s: %s",
                user_id,
                review_date,
                e,
            )
            raise

    def get_review_log_by_month(
        self, user_id: int, month: str, year: int
    ) -> Dict[int, int]:
        """Fetch the review log for the specified month and year."""
        logger.info(
            "Fetching review log for user_id: %d, month: %s, year: %d",
            user_id,
            month,
            year,
        )

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")
        if not isinstance(month, str):
            logger.error("Invalid month provided: %s", month)
            raise ValueError(f"Invalid month: {month}")
        if not isinstance(year, int) or year <= 0:
            logger.error("Invalid year provided: %d", year)
            raise ValueError(f"Invalid year: {year}")

        try:
            query = """
                SELECT review_date, reviewed_cards_count
                FROM DailyReviewLog
                WHERE user_id = ? AND strftime('%m', review_date) = ? AND strftime('%Y', review_date) = ?
            """
            month_number = {
                "January": "01",
                "February": "02",
                "March": "03",
                "April": "04",
                "May": "05",
                "June": "06",
                "July": "07",
                "August": "08",
                "September": "09",
                "October": "10",
                "November": "11",
                "December": "12",
            }.get(month)
            if not month_number:
                logger.error("Invalid month name provided: %s", month)
                raise ValueError(f"Invalid month name: {month}")

            results = self.fetch(query, (user_id, month_number, str(year)))
            review_log = {
                int(result["review_date"].split("-")[2]): result["reviewed_cards_count"]
                for result in results
            }
            logger.info(
                "Fetched review log for user_id: %d for %s %d: %s",
                user_id,
                month,
                year,
                review_log,
            )
            return review_log
        except Exception as e:
            logger.error(
                "Error fetching review log for user_id %d in %s %d: %s",
                user_id,
                month,
                year,
                e,
            )
            raise
