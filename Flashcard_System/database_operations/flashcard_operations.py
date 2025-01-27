from abc import ABC
from datetime import datetime
from typing import List, Dict, Any, Tuple

import logging

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


class FlashcardOperations(BaseDatabaseOperations, ABC):
    def fetch(self, query: str, params: Tuple = ()) -> List[Any]:
        """Fetch multiple rows from the database."""
        try:
            return super().fetch(query, params)
        except Exception as e:
            logger.error("Error fetching data in FlashcardOperations: %s", e)
            raise

    def fetch_one(self, query: str, params: Tuple = ()) -> Dict[str, Any]:
        """Fetch a single row from the database."""
        try:
            return super().fetch_one(query, params)
        except Exception as e:
            logger.error("Error fetching one row in FlashcardOperations: %s", e)
            raise

    def insert(self, query: str, params: Tuple = ()) -> None:
        """Insert data into the database."""
        try:
            super().insert(query, params)
        except Exception as e:
            logger.error("Error inserting data in FlashcardOperations: %s", e)
            raise

    def update(self, query: str, params: Tuple = ()) -> None:
        """Update data in the database."""
        try:
            super().update(query, params)
        except Exception as e:
            logger.error("Error updating data in FlashcardOperations: %s", e)
            raise

    def delete(self, query: str, params: Tuple = ()) -> None:
        """Delete data from the database."""
        try:
            super().delete(query, params)
        except Exception as e:
            logger.error("Error deleting data in FlashcardOperations: %s", e)
            raise

    def create_flashcard(
        self, user_id: int, flashcard_data: Dict[str, Any], next_review_date: datetime
    ) -> None:
        """Create a new flashcard for a user."""
        logger.info("Creating flashcard for user_id: %d", user_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        required_keys = ["set_name", "front", "back"]
        for key in required_keys:
            if key not in flashcard_data:
                logger.error("Missing %s in flashcard data", key)
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
                logger.error("Failed to retrieve next card ID for user %d", user_id)
                raise RuntimeError(
                    f"Failed to retrieve next card ID for user {user_id}"
                )

            next_card_id = next_card_id["next_card_id"]
            logger.info("Next card_id for user %d: %d", user_id, next_card_id)

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
            logger.error("Error creating flashcard for user %d: %s", user_id, e)
            raise

        try:
            insert_user_performance_query = """
                INSERT INTO UserPerformance (user_id, card_id, review_time, next_review_date)
                VALUES (?, ?, ?, ?)
            """
            params = (
                user_id,
                next_card_id,
                next_review_date.strftime("%Y-%m-%d"),
                next_review_date.strftime("%Y-%m-%d"),
            )
            self.insert(insert_user_performance_query, params)
            logger.info(
                "User performance record created successfully for user_id: %d, card_id: %d",
                user_id,
                next_card_id,
            )
        except Exception as e:
            logger.error(
                "Error creating user performance record for user %d: %s", user_id, e
            )
            raise

    def fetch_due_cards(
        self, user_id: int, review_date: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch due flashcards based on the review date and limit."""
        logger.info(
            "Fetching due cards for user_id: %d, review_date: %s, limit: %d",
            user_id,
            review_date,
            limit,
        )

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        if not isinstance(limit, int) or limit <= 0:
            logger.error("Invalid limit provided: %d", limit)
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
            due_cards = self.fetch(query, (user_id, review_date, limit))
            logger.info(
                "Fetched %d due cards for user_id: %d on review_date: %s",
                len(due_cards),
                user_id,
                review_date,
            )
            return due_cards
        except Exception as e:
            logger.error("Error fetching due cards for user %d: %s", user_id, e)
            raise

    def fetch_card_by_id(self, card_id: int) -> Dict[str, Any]:
        """Fetch a single flashcard's details by its card_id."""
        logger.info("Fetching flashcard with card_id: %d", card_id)

        if not isinstance(card_id, int) or card_id <= 0:
            logger.error("Invalid card_id provided: %d", card_id)
            raise ValueError(f"Invalid card_id: {card_id}")

        try:
            query = """
                SELECT card_id, user_id, set_name, front, back
                FROM Flashcards
                WHERE card_id = ?
            """
            card = self.fetch_one(query, (card_id,))
            if card:
                logger.info("Flashcard fetched successfully for card_id: %d", card_id)
            else:
                logger.warning("No flashcard found for card_id: %d", card_id)
            return card
        except Exception as e:
            logger.error("Error fetching flashcard with card_id %d: %s", card_id, e)
            raise

    def fetch_flashcards_by_set(
        self, user_id: int, set_name: str
    ) -> List[Dict[str, Any]]:
        """Fetch flashcards by set name."""
        logger.info(
            "Fetching flashcards by set_name: %s for user_id: %d", set_name, user_id
        )

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        if not isinstance(set_name, str) or not set_name.strip():
            logger.error("Invalid set_name provided: %s", set_name)
            raise ValueError(f"Invalid set_name: {set_name}")

        try:
            query = """
                SELECT card_id, front, back
                FROM Flashcards
                WHERE user_id = ? AND set_name = ?
            """
            flashcards = self.fetch(query, (user_id, set_name))
            logger.info(
                "Fetched %d flashcards for user_id: %d in set_name: %s",
                len(flashcards),
                user_id,
                set_name,
            )
            return flashcards
        except Exception as e:
            logger.error("Error fetching flashcards by set_name %s: %s", set_name, e)
            raise

    def fetch_sets(self, user_id: int) -> List[str]:
        """Fetch all flashcard sets for a user."""
        logger.info("Fetching flashcard sets for user_id: %d", user_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        try:
            query = """
                SELECT DISTINCT set_name
                FROM Flashcards
                WHERE user_id = ?
            """
            sets = self.fetch(query, (user_id,))
            logger.info("Fetched %d sets for user_id: %d", len(sets), user_id)
            return [set["set_name"] for set in sets]
        except Exception as e:
            logger.error("Error fetching flashcard sets for user %d: %s", user_id, e)
            raise

    def delete_card(self, user_id: int, card_id: int):
        """Delete a flashcard from Flashcards Table using card id."""
        logger.info("Deleting flashcard for user_id: %d, card_id: %d", user_id, card_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        if not isinstance(card_id, int) or card_id <= 0:
            logger.error("Invalid card_id provided: %d", card_id)
            raise ValueError(f"Invalid card_id: {card_id}")

        try:
            query = """
                DELETE FROM Flashcards
                WHERE user_id = ? AND card_id = ?
            """
            self.delete(query, (user_id, card_id))
            logger.info(
                "Flashcard deleted successfully for user_id: %d, card_id: %d",
                user_id,
                card_id,
            )
        except Exception as e:
            logger.error("Error deleting flashcard for user %d: %s", user_id, e)
            raise

    def delete_set(self, user_id: int, set_name: str):
        """Delete a flashcard set."""
        logger.info(
            "Deleting flashcard set for user_id: %d, set_name: %s", user_id, set_name
        )

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        if not isinstance(set_name, str) or not set_name.strip():
            logger.error("Invalid set_name provided: %s", set_name)
            raise ValueError(f"Invalid set_name: {set_name}")

        try:
            query = """
                DELETE FROM Flashcards
                WHERE user_id = ? AND set_name = ?
            """
            self.delete(query, (user_id, set_name))
            logger.info(
                "Flashcard set deleted successfully for user_id: %d, set_name: %s",
                user_id,
                set_name,
            )
        except Exception as e:
            logger.error("Error deleting flashcard set for user %d: %s", user_id, e)
            raise

    def get_card_id_for_set(self, user_id: int, set_name: str) -> List[int]:
        """Fetch card IDs for a given set."""
        logger.info("Fetching card IDs for set: %s, user_id: %d", set_name, user_id)

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        if not isinstance(set_name, str) or not set_name.strip():
            logger.error("Invalid set_name provided: %s", set_name)
            raise ValueError(f"Invalid set_name: {set_name}")

        try:
            query = """
                SELECT card_id
                FROM Flashcards
                WHERE user_id = ? AND set_name = ?
            """
            cards = self.fetch(query, (user_id, set_name))
            card_ids = [card["card_id"] for card in cards]
            logger.info(
                "Fetched %d card IDs for user_id: %d in set_name: %s",
                len(card_ids),
                user_id,
                set_name,
            )
            return card_ids
        except Exception as e:
            logger.error(
                "Error fetching card IDs for set %s, user_id %d: %s",
                set_name,
                user_id,
                e,
            )
            raise

    def update_flashcard(self, user_id: int, flashcard: Dict[str, Any]):
        """Update an existing flashcard."""
        logger.info(
            "Updating flashcard for user_id: %d, card_id: %d",
            user_id,
            flashcard.get("card_id", -1),
        )

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Invalid user_id provided: %d", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        required_keys = ["card_id", "front", "back"]
        for key in required_keys:
            if key not in flashcard:
                logger.error(
                    "Missing %s in flashcard data for user_id: %d", key, user_id
                )
                raise ValueError(f"Missing {key} in flashcard data")

        try:
            query = """
                UPDATE Flashcards
                SET front = ?, back = ?
                WHERE user_id = ? AND card_id = ?
            """
            params = (
                flashcard["front"],
                flashcard["back"],
                user_id,
                flashcard["card_id"],
            )
            self.update(query, params)
            logger.info(
                "Flashcard updated successfully for user_id: %d, card_id: %d",
                user_id,
                flashcard["card_id"],
            )
        except Exception as e:
            logger.error(
                "Error updating flashcard for user_id %d, card_id %d: %s",
                user_id,
                flashcard["card_id"],
                e,
            )
            raise
