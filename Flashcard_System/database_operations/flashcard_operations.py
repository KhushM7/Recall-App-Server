from abc import ABC
from typing import List, Dict, Any, Tuple

import logging

from Flashcard_System.database_operations.base_database_operations import (
    BaseDatabaseOperations,
)


class FlashcardOperations(BaseDatabaseOperations, ABC):
    def fetch(self, query: str, params: Tuple = ()) -> List[Any]:
        """Fetch multiple rows from the database."""
        try:
            return super().fetch(query, params)
        except Exception as e:
            logging.error(f"Error fetching data in FlashcardOperations: {e}")
            raise

    def fetch_one(self, query: str, params: Tuple = ()) -> Dict[str, Any]:
        """Fetch a single row from the database."""
        try:
            return super().fetch_one(query, params)
        except Exception as e:
            logging.error(f"Error fetching one row in FlashcardOperations: {e}")
            raise

    def insert(self, query: str, params: Tuple = ()) -> None:
        """Insert data into the database."""
        try:
            super().insert(query, params)
        except Exception as e:
            logging.error(f"Error inserting data in FlashcardOperations: {e}")
            raise

    def update(self, query: str, params: Tuple = ()) -> None:
        """Update data in the database."""
        try:
            super().update(query, params)
        except Exception as e:
            logging.error(f"Error updating data in FlashcardOperations: {e}")
            raise

    def create_flashcard(self, user_id: int, flashcard_data: Dict[str, Any]) -> None:
        """Create a new flashcard for a user."""
        logging.info(f"Creating flashcard for user_id: {user_id}")

        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")

        required_keys = ["set_name", "front", "back"]
        for key in required_keys:
            if key not in flashcard_data:
                raise ValueError(f"Missing {key} in flashcard data")

        try:
            # Fetch next available card_id for the user
            query = """
                SELECT COALESCE(MAX(card_id), 0) + 1 AS next_card_id
                FROM Flashcards
                WHERE user_id = ?
            """
            next_card_id = self.fetch_one(query, (user_id,))
            if not next_card_id:
                raise RuntimeError(
                    f"Failed to retrieve next card ID for user {user_id}"
                )

            next_card_id = next_card_id["next_card_id"]
            logging.info(f"Next card_id for user {user_id}: {next_card_id}")

            insert_flashcard_query = """
                INSERT INTO Flashcards (user_id, card_id, set_name, front, back)
                VALUES (?, ?, ?, ?, ?)
            """
            params = (
                user_id,
                next_card_id,
                flashcard_data["set_name"],
                flashcard_data["front"],
                flashcard_data["back"],
            )
            self.insert(insert_flashcard_query, params)
        except Exception as e:
            logging.error(f"Error creating flashcard for user {user_id}: {e}")
            raise

    def fetch_due_cards(
        self, user_id: int, review_date: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch due flashcards based on the review date and limit."""
        logging.info(
            f"Fetching due cards for user_id: {user_id}, review_date: {review_date}, limit: {limit}"
        )

        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")

        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"Invalid limit: {limit}")

        try:
            query = """
                SELECT f.card_id, f.set_name, f.front, f.back
                FROM Flashcards f
                JOIN UserPerformance u ON f.user_id = u.user_id AND f.card_id = u.card_id
                WHERE u.user_id = ? AND u.next_review_date <= ?
                ORDER BY u.priority DESC, u.next_review_date ASC
                LIMIT ?
            """
            return self.fetch(query, (user_id, review_date, limit))
        except Exception as e:
            logging.error(f"Error fetching due cards for user {user_id}: {e}")
            raise
