import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class DatabaseOperations:
    def __init__(self, db_path: str):
        """Initialize the database connection."""
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # To fetch rows as dictionaries

    def fetch_due_cards(self, user_id: int, review_date: str, limit: int) -> List[Dict]:
        """
        Fetch due cards, prioritizing cards that were carried over (priority = 1).
        This function now accepts the review date to fetch cards due on or before that date.
        """
        cursor = self.conn.execute(
            """
            SELECT f.card_id, f.set_name, f.front, f.back
            FROM Flashcards f
            JOIN UserPerformance u ON f.user_id = u.user_id AND f.card_id = u.card_id
            WHERE u.user_id = ? AND u.next_review_date <= ?
            ORDER BY u.priority DESC, u.next_review_date ASC
            LIMIT ?
            """,
            (user_id, review_date, limit),
        )

        return [dict(row) for row in cursor.fetchall()]

    def create_flashcard(self, user_id: int, flashcard_data: Dict) -> None:
        """
        Create a new flashcard for the user. Automatically increments the card_id based on the user.
        """
        # Get the maximum card_id for this user and increment it
        cursor = self.conn.execute(
            """
            SELECT COALESCE(MAX(card_id), 0) + 1 AS next_card_id
            FROM Flashcards
            WHERE user_id = ?
        """,
            (user_id,),
        )

        next_card_id = cursor.fetchone()["next_card_id"]

        # Insert the new flashcard into the Flashcards table
        self.conn.execute(
            """
            INSERT INTO Flashcards (user_id, card_id, set_name, front, back)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                user_id,
                next_card_id,
                flashcard_data["set_name"],
                flashcard_data["front"],
                flashcard_data["back"],
            ),
        )
        # Insert a corresponding entry into UserPerformance for this user's new card
        self.conn.execute(
            """
                INSERT INTO UserPerformance (user_id, card_id, stability, difficulty, rating, 
                                             scheduled_days, elapsed_days, review_time, next_review_date, state, reps, lapses)
                VALUES (?, ?, 0, 0, 0, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 0, 0)
            """,
            (user_id, next_card_id),
        )
        self.conn.commit()  # Commit the changes to the database

    def fetch_daily_review_limit(self, user_id: int) -> int:
        """Fetch the daily review limit for the user from the UserSettings table."""
        cursor = self.conn.execute(
            """
            SELECT daily_review_limit 
            FROM UserSettings 
            WHERE user_id = ?
        """,
            (user_id,),
        )

        result = cursor.fetchone()
        return result["daily_review_limit"]

    def fetch_reviewed_today(self, user_id: int, review_date: str) -> int:
        """Fetch how many cards the user has already reviewed today."""
        cursor = self.conn.execute(
            """
            SELECT reviewed_cards_count 
            FROM DailyReviewLog 
            WHERE user_id = ? AND review_date = ?
        """,
            (user_id, review_date),
        )

        result = cursor.fetchone()
        if result:
            return result["reviewed_cards_count"]
        else:
            return 0  # No reviews yet today

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
            f"Inserting into DB: Next Review: {card_data['next_review_date']} (Card ID {card_data['card_id']})"
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

    def increment_reviewed_card_count(self, user_id: int, review_date: str) -> None:
        """Increment the count of reviewed cards for the user in the DailyReviewLog."""
        self.conn.execute(
            """
            INSERT INTO DailyReviewLog (user_id, review_date, reviewed_cards_count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, review_date)
            DO UPDATE SET reviewed_cards_count = reviewed_cards_count + 1;
        """,
            (user_id, review_date),
        )

    def mark_cards_as_priority(self, user_id: int, review_date: str) -> None:
        """
        Mark unreviewed cards as priority and increment their priority level,
        also update their next review date to the next day.
        """
        # Calculate the next day
        next_day = (
            (datetime.strptime(review_date, "%Y-%m-%d") + timedelta(days=1))
            .date()
            .isoformat()
        )

        # Increment priority and update next review date for unreviewed cards
        self.conn.execute(
            """
            UPDATE UserPerformance
            SET priority = priority + 1, next_review_date = ?
            WHERE user_id = ? AND next_review_date <= ? AND priority >= 0
        """,
            (next_day, user_id, review_date),
        )

        self.conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
