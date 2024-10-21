import sqlite3
from typing import List, Dict, Optional


class DatabaseOperations:
    def __init__(self, db_path: str):
        """Initialize the database connection."""
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # To fetch rows as dictionaries

    def fetch_flashcards(self) -> List[Dict]:
        """Fetch all flashcards from the Flashcard table."""
        cursor = self.conn.execute("SELECT * FROM Flashcards")
        return [dict(row) for row in cursor.fetchall()]

    def store_review_result(self, user_id: int, card_data: Dict) -> None:
        """
        Store the review result for a user in the UserPerformance table.

        Args:
            user_id (int): The ID of the user.
            card_data (Dict): A dictionary containing review result data.
                Must contain the following keys:
                - card_id (int)
                - rating (int)
                - scheduled_days (int)
                - elapsed_days (int)
                - review_time (datetime)
                - state (int)
                - next_review_date (datetime)
        """
        print(
            f"Inserting into DB: State: {card_data['state']} (Card ID {card_data['card_id']})"
        )
        # print(
        #     f"""
        #     UserID: {user_id},
        #     CardID: {card_data['card_id']},
        #     Stability: {card_data['stability']},
        #     Difficulty: {card_data['difficulty']},
        #     Scheduled Days: {card_data['scheduled_days']},
        #     Elapsed Days: {card_data['elapsed_days']},
        #     State: {card_data['state']},
        #     Reps: {card_data['reps']},
        #     Lapses: {card_data['lapses']}
        # """
        # )
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO UserPerformance (
                    user_id, card_id, stability, difficulty, rating, scheduled_days, elapsed_days, 
                    review_time, next_review_date, state, reps, lapses
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
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
                ),
            )

    def fetch_user_performance(self, user_id: int, card_id: int) -> Optional[Dict]:
        """Fetch the performance data of a user for a specific card."""
        cursor = self.conn.execute(
            """
            SELECT * FROM UserPerformance
            WHERE user_id = ? AND card_id = ?
        """,
            (user_id, card_id),
        )

        result = cursor.fetchone()
        return dict(result) if result else None

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
