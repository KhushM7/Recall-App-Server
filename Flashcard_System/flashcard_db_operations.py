import sqlite3
from datetime import datetime
from typing import Any, Optional, Union
from enum import IntEnum


class DatabaseOperations:
    def __init__(self, db_name: str = "fsrs.db"):
        self.conn = sqlite3.connect(db_name)

    def save_card(self, card: Card) -> int:
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                # INSERT INTO Flashcards (due, stability, difficulty, elapsed_days, scheduled_days, reps, lapses, state, last_review)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    card.due.isoformat(),
                    card.stability,
                    card.difficulty,
                    card.elapsed_days,
                    card.scheduled_days,
                    card.reps,
                    card.lapses,
                    card.state.value,
                    card.last_review.isoformat() if card.last_review else None,
                ),
            )
            return cursor.lastrowid

    def save_review_log(self, card_id: int, review_log: ReviewLog) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO ReviewLogs (user_id, card_id, rating, scheduled_days, elapsed_days, review, state)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    card_id,
                    review_log.rating.value,
                    review_log.scheduled_days,
                    review_log.elapsed_days,
                    review_log.review.isoformat(),
                    review_log.state.value,
                ),
            )

    def load_card(self, card_id: int) -> Optional[Card]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Flashcards WHERE flashcard_id = ?", (card_id,))
        row = cursor.fetchone()
        if row:
            return Card.from_dict(
                {
                    "due": row[1],
                    "stability": row[2],
                    "difficulty": row[3],
                    "elapsed_days": row[4],
                    "scheduled_days": row[5],
                    "reps": row[6],
                    "lapses": row[7],
                    "state": row[8],
                    "last_review": row[9],
                }
            )
        return None

    def load_review_logs(self, card_id: int, user_id: int) -> list[ReviewLog]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM ReviewLogs WHERE card_id = ? AND user_id = ?",
            (
                card_id,
                user_id,
            ),
        )
        rows = cursor.fetchall()
        return [
            ReviewLog.from_dict(
                {
                    "rating": row[2],
                    "scheduled_days": row[3],
                    "elapsed_days": row[4],
                    "review": row[5],
                    "state": row[6],
                }
            )
            for row in rows
        ]
