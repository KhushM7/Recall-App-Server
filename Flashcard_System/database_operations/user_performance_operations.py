import logging
from abc import ABC
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta

from Flashcard_System.database_operations.base_database_operations import (
    BaseDatabaseOperations,
)


class UserPerformanceOperations(BaseDatabaseOperations, ABC):
    def fetch(self, query: str, params: Tuple = ()) -> List[Any]:
        """Fetch multiple rows from the database."""
        try:
            return super().fetch(query, params)
        except Exception as e:
            logging.error(f"Error fetching data in UserPerformanceOperations: {e}")
            raise

    def fetch_one(self, query: str, params: Tuple = ()) -> Dict[str, Any]:
        """Fetch a single row from the database."""
        try:
            return super().fetch_one(query, params)
        except Exception as e:
            logging.error(f"Error fetching one row in UserPerformanceOperations: {e}")
            raise

    def insert(self, query: str, params: Tuple = ()) -> None:
        """Insert data into the database."""
        try:
            super().insert(query, params)
        except Exception as e:
            logging.error(f"Error inserting data in UserPerformanceOperations: {e}")
            raise

    def update(self, query: str, params: Tuple = ()) -> None:
        """Update data in the database."""
        try:
            super().update(query, params)
        except Exception as e:
            logging.error(f"Error updating data in UserPerformanceOperations: {e}")
            raise

    def delete(self, query: str, params: Tuple = ()) -> None:
        """Delete data from the database."""
        try:
            super().delete(query, params)
        except Exception as e:
            logging.error(f"Error deleting data in UserPerformanceOperations: {e}")
            raise

    def store_review_result(self, user_id: int, card_data: Dict[str, Any]) -> None:
        """Store the review result for a user's card."""
        logging.info(
            f"Storing review result for user_id: {user_id}, card_id: {card_data['card_id']}"
        )

        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")

        required_keys = [
            "card_id",
            "stability",
            "difficulty",
            "rating",
            "scheduled_days",
            "elapsed_days",
            "review_time",
            "next_review_date",
            "state",
            "reps",
            "lapses",
        ]
        for key in required_keys:
            if key not in card_data:
                raise ValueError(f"Missing {key} in card_data")

        try:
            query = """
                INSERT OR REPLACE INTO UserPerformance (
                    user_id, card_id, stability, difficulty, rating, scheduled_days, 
                    elapsed_days, review_time, next_review_date, state, reps, lapses
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                user_id,
                card_data["card_id"],
                card_data["stability"],
                card_data["difficulty"],
                card_data["rating"],
                card_data["scheduled_days"],
                card_data["elapsed_days"],
                card_data["review_time"].isoformat(),
                card_data["next_review_date"].isoformat(),
                card_data["state"],
                card_data["reps"],
                card_data["lapses"],
            )
            self.insert(query, params)
        except Exception as e:
            logging.error(
                f"Error storing review result for user {user_id}, card {card_data['card_id']}: {e}"
            )
            raise

    def mark_cards_as_priority(
        self, user_id: int, review_date: str, mark_today: bool = False
    ) -> None:
        """
        Mark unreviewed cards as priority and update their next review date. If `mark_today` is True,
        it marks cards that were due today (priority 0) as priority and pushes their review date to tomorrow.

        Args:
            user_id: The ID of the user.
            review_date: The date to compare with card due dates.
            mark_today: If True, mark cards that were due today and have priority 0.
        """
        logging.info(
            f"Marking unreviewed cards as priority for user_id: {user_id}, review_date: {review_date}"
        )

        next_day = (
            (datetime.strptime(review_date, "%Y-%m-%d") + timedelta(days=1))
            .date()
            .isoformat()
        )

        if mark_today:
            logging.info(
                f"Marking today’s unreviewed cards as priority 1 for user_id: {user_id}, review_date: {review_date}"
            )
            query_today = """
                UPDATE UserPerformance
                SET priority = 1, next_review_date = ?
                WHERE user_id = ? AND next_review_date = ? AND priority = 0
            """
            self.update(query_today, (next_day, user_id, review_date))
        else:
            logging.info(
                f"Incrementing priority for unreviewed cards before {review_date} for user_id: {user_id}"
            )
            query_past = """
                UPDATE UserPerformance
                SET priority = priority + 1, next_review_date = ?
                WHERE user_id = ? AND next_review_date < ? AND priority >= 0
            """
            self.update(query_past, (next_day, user_id, review_date))

    def fetch_user_performance(
        self, user_id: int, card_id: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch the performance data of a specific card for a user."""
        logging.info(
            f"Fetching user performance for user_id: {user_id}, card_id: {card_id}"
        )
        query = """
            SELECT * FROM UserPerformance
            WHERE user_id = ? AND card_id = ?
        """
        return self.fetch_one(query, (user_id, card_id))

    def delete_card(self, user_id: int, card_id: int):
        """Delete a flashcard from UserPerformance Table using card id."""
        logging.info(f"Deleting flashcard for user_id: {user_id}")

        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")

        if not isinstance(card_id, int) or card_id <= 0:
            raise ValueError(f"Invalid card id: {card_id}")

        try:
            query = """
                DELETE FROM UserPerformance
                WHERE user_id = ? AND card_id = ?
            """
            self.delete(query, (user_id, card_id))
        except Exception as e:
            logging.error(f"Error deleting flashcard for user {user_id}: {e}")
            raise

    def delete_set(self, user_id: int, card_id_for_set: list):
        """Delete a flashcard set from UserPerformance Table using card id's."""
        logging.info(f"Deleting flashcard set for user_id: {user_id}")

        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")

        if not isinstance(card_id_for_set, list) or len(card_id_for_set) == 0:
            raise ValueError(f"Invalid card id's: {card_id_for_set}")

        try:
            query = """
                DELETE FROM UserPerformance
                WHERE user_id = ? AND card_id = ?
            """
            for card_id in card_id_for_set:
                self.delete(query, (user_id, card_id))
        except Exception as e:
            logging.error(f"Error deleting flashcard set for user {user_id}: {e}")
            raise
