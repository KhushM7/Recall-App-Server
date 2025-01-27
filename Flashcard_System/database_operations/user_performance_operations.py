import logging
from abc import ABC
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta

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


class UserPerformanceOperations(BaseDatabaseOperations, ABC):
    def fetch(self, query: str, params: Tuple = ()) -> List[Any]:
        """Fetch multiple rows from the database."""
        try:
            return super().fetch(query, params)
        except Exception as e:
            logger.error("Error fetching data in UserPerformanceOperations: %s", e)
            raise

    def fetch_one(self, query: str, params: Tuple = ()) -> Dict[str, Any]:
        """Fetch a single row from the database."""
        try:
            return super().fetch_one(query, params)
        except Exception as e:
            logger.error("Error fetching one row in UserPerformanceOperations: %s", e)
            raise

    def insert(self, query: str, params: Tuple = ()) -> None:
        """Insert data into the database."""
        try:
            super().insert(query, params)
        except Exception as e:
            logger.error("Error inserting data in UserPerformanceOperations: %s", e)
            raise

    def update(self, query: str, params: Tuple = ()) -> None:
        """Update data in the database."""
        try:
            super().update(query, params)
        except Exception as e:
            logger.error("Error updating data in UserPerformanceOperations: %s", e)
            raise

    def delete(self, query: str, params: Tuple = ()) -> None:
        """Delete data from the database."""
        try:
            super().delete(query, params)
        except Exception as e:
            logger.error("Error deleting data in UserPerformanceOperations: %s", e)
            raise

    def store_review_result(self, user_id: int, card_data: Dict[str, Any]) -> None:
        """Store the review result for a user's card."""
        logger.info(
            "Storing review result for user_id: %d, card_id: %d",
            user_id,
            card_data["card_id"],
        )

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
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
                logger.error("Missing %s in card_data", key)
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
            logger.info("Review result stored successfully for user_id: %d", user_id)
        except Exception as e:
            logger.error(
                "Error storing review result for user_id %d, card_id %d: %s",
                user_id,
                card_data["card_id"],
                e,
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
        logger.info(
            "Marking unreviewed cards as priority for user_id: %d, review_date: %s",
            user_id,
            review_date,
        )

        next_day = (
            (datetime.strptime(review_date, "%Y-%m-%d") + timedelta(days=1))
            .date()
            .isoformat()
        )

        if mark_today:
            logger.info(
                "Marking today’s unreviewed cards as priority 1 for user_id: %d, review_date: %s",
                user_id,
                review_date,
            )
            query_today = """
                UPDATE UserPerformance
                SET priority = 1, next_review_date = ?
                WHERE user_id = ? AND next_review_date = ? AND priority = 0
            """
            self.update(query_today, (next_day, user_id, review_date))
        else:
            logger.info(
                "Incrementing priority for unreviewed cards before %s for user_id: %d",
                review_date,
                user_id,
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
        logger.info(
            "Fetching user performance for user_id: %d, card_id: %d", user_id, card_id
        )
        query = """
            SELECT * FROM UserPerformance
            WHERE user_id = ? AND card_id = ?
        """
        return self.fetch_one(query, (user_id, card_id))

    def delete_card(self, user_id: int, card_id: int):
        """Delete a flashcard from UserPerformance Table using card id."""
        logger.info("Deleting flashcard for user_id: %d, card_id: %d", user_id, card_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        if not isinstance(card_id, int) or card_id <= 0:
            logger.error("Invalid card_id provided: %d", card_id)
            raise ValueError(f"Invalid card id: {card_id}")

        try:
            query = """
                DELETE FROM UserPerformance
                WHERE user_id = ? AND card_id = ?
            """
            self.delete(query, (user_id, card_id))
            logger.info(
                "Flashcard deleted successfully for user_id: %d, card_id: %d",
                user_id,
                card_id,
            )
        except Exception as e:
            logger.error(
                "Error deleting flashcard for user_id %d, card_id %d: %s",
                user_id,
                card_id,
                e,
            )
            raise

    def delete_set(self, user_id: int, card_id_for_set: list):
        """Delete a flashcard set from UserPerformance Table using card id's."""
        logger.info("Deleting flashcard set for user_id: %d", user_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        if not isinstance(card_id_for_set, list) or len(card_id_for_set) == 0:
            logger.error("Invalid card_id_for_set provided: %s", card_id_for_set)
            raise ValueError(f"Invalid card id's: {card_id_for_set}")

        try:
            query = """
                DELETE FROM UserPerformance
                WHERE user_id = ? AND card_id = ?
            """
            for card_id in card_id_for_set:
                self.delete(query, (user_id, card_id))
            logger.info("Flashcard set deleted successfully for user_id: %d", user_id)
        except Exception as e:
            logger.error("Error deleting flashcard set for user_id %d: %s", user_id, e)
            raise

    def get_next_reviews_by_month(self, user_id: int, month: str, year: int):
        """Fetch the next review dates for a specific month and year."""
        import calendar

        logger.info(
            "Fetching next review dates for user_id: %d, month: %s, year: %d",
            user_id,
            month,
            year,
        )

        # Validate input
        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")
        if not isinstance(month, str) or not month.strip():
            logger.error("Invalid month provided: %s", month)
            raise ValueError(f"Invalid month: {month}")
        if not isinstance(year, int) or year <= 0:
            logger.error("Invalid year provided: %d", year)
            raise ValueError(f"Invalid year: {year}")

        # Convert month name to two-digit number
        try:
            month_number = f"{list(calendar.month_name).index(month):02}"
        except ValueError:
            logger.error("Invalid month name provided: %s", month)
            raise ValueError(f"Invalid month name: {month}")

        try:
            query = """
                SELECT 
                    substr(next_review_date, 9, 2) AS day_of_month, 
                    COUNT(card_id) AS card_count 
                FROM UserPerformance 
                WHERE user_id = ? 
                  AND next_review_date LIKE ? 
                GROUP BY day_of_month
            """

            results = self.fetch(
                query,
                (
                    user_id,
                    f"{year}-{month_number}%",
                ),
            )

            # Convert the results into a dictionary
            return {
                int(entry["day_of_month"]): entry["card_count"] for entry in results
            }

        except Exception as e:
            logger.error(
                "Error fetching next review dates for user_id %d in %s %d: %s",
                user_id,
                month,
                year,
                e,
            )
            raise

    def get_all_current_card_states(self, user_id: int) -> Dict[str, Any]:
        """Fetch all current card states for a user."""
        logger.info("Fetching all current card states for user_id: %d", user_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        try:
            query = """
                SELECT state, COUNT(card_id) AS count
                FROM UserPerformance
                WHERE user_id = ?
                GROUP BY state
            """
            results = self.fetch(query, (user_id,))

            # Map the state numbers to their corresponding names
            state_mapping = {0: "New", 1: "Learning", 2: "Review", 3: "Relearning"}
            state_counts = {
                state_mapping[row["state"]]: row["count"] for row in results
            }

            return state_counts
        except Exception as e:
            logger.error(
                "Error fetching current card states for user_id %d: %s", user_id, e
            )
            raise

    def get_total_lapses(self, user_id: int) -> int:
        """Fetch the total number of lapses for a user."""
        logger.info("Fetching total lapses for user_id: %d", user_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        try:
            query = """
                    SELECT SUM(lapses) AS total_lapses
                    FROM UserPerformance
                    WHERE user_id = ?
                """
            result = self.fetch_one(query, (user_id,))
            total_lapses = (
                result["total_lapses"] if result and result["total_lapses"] else 0
            )
            logger.info(
                "Total lapses for user_id %d fetched successfully: %d",
                user_id,
                total_lapses,
            )
            return total_lapses
        except Exception as e:
            logger.error("Error fetching total lapses for user_id %d: %s", user_id, e)
            raise

    def get_stability_data(self, user_id: int) -> Dict[str, Any]:
        """Fetch the stability data for a user."""
        logger.info("Fetching stability data for user_id: %d", user_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        try:
            query = """
                    SELECT stability, card_id
                    FROM UserPerformance
                    WHERE user_id = ?
                """
            results = self.fetch(query, (user_id,))
            stability_data = {row["card_id"]: row["stability"] for row in results}
            logger.info(
                "Stability data fetched for user_id %d: %s", user_id, stability_data
            )
            return stability_data
        except Exception as e:
            logger.error("Error fetching stability data for user_id %d: %s", user_id, e)
            raise

    def get_difficulty_data(self, user_id: int) -> Dict[str, Any]:
        """Fetch the difficulty data for a user."""
        logger.info("Fetching difficulty data for user_id: %d", user_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        try:
            query = """
                    SELECT difficulty, card_id
                    FROM UserPerformance
                    WHERE user_id = ?
                """
            results = self.fetch(query, (user_id,))
            difficulty_data = {row["card_id"]: row["difficulty"] for row in results}
            logger.info(
                "Difficulty data fetched for user_id %d: %s", user_id, difficulty_data
            )
            return difficulty_data
        except Exception as e:
            logger.error(
                "Error fetching difficulty data for user_id %d: %s", user_id, e
            )
            raise

    def get_current_ratings(self, user_id: int) -> Dict[str, Any]:
        """Fetch the current ratings for a user."""
        logger.info("Fetching current ratings for user_id: %d", user_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        try:
            query = """
                    SELECT rating, COUNT(card_id) as count
                    FROM UserPerformance
                    WHERE user_id = ?
                    GROUP BY rating
                """
            results = self.fetch(query, (user_id,))
            rating_mapping = {
                0: "Not Reviewed",
                1: "Again",
                2: "Hard",
                3: "Good",
                4: "Easy",
            }
            rating_counts = {
                rating_mapping[row["rating"]]: row["count"] for row in results
            }
            logger.info(
                "Current ratings fetched for user_id %d: %s", user_id, rating_counts
            )
            return rating_counts
        except Exception as e:
            logger.error(
                "Error fetching current ratings for user_id %d: %s", user_id, e
            )
            raise
