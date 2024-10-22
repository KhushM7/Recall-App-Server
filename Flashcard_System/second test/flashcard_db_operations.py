import sqlite3
from Flashcard_System.flashcard_models import Card, ReviewLog


class DatabaseOperations:
    def __init__(self, db_path: str = "../physics_revision_app.db"):
        self.db_path = db_path

    def get_flashcard(self, card_id: int) -> Card | None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT card_id, set_name, front, back
                    FROM Flashcards1
                    WHERE card_id = ?
                    """,
                    (card_id,),
                )
                row = cursor.fetchone()
                if row:
                    return Card(
                        card_id=row[0], set_name=row[1], front=row[2], back=row[3]
                    )
                print(f"Flashcard with ID {card_id} not found.")
                return None
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        return None

    def save_review_log(
        self, user_id: int, card_id: int, review_log: ReviewLog
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            print(
                f"""
                            UserID: {user_id},
                            CardID: {card_id},
                            Stability: {review_log.stability},
                            Difficulty: {review_log.difficulty},
                            Rating: {review_log.rating.value},
                            Scheduled Days: {review_log.scheduled_days},
                            Elapsed Days: {review_log.elapsed_days},
                            Review: {review_log.review.isoformat()},
                            State: {review_log.state.value},
                            Reps: {review_log.reps},
                            Lapses: {review_log.lapses}
                        """
            )
            cursor.execute(
                """
                INSERT INTO UserPerformance (
                    user_id, card_id, stability, difficulty, rating, scheduled_days, elapsed_days, review, state, reps, lapses
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(user_id, card_id) DO UPDATE SET
                    stability=excluded.stability,
                    difficulty=excluded.difficulty,
                    rating=excluded.rating,
                    scheduled_days=excluded.scheduled_days,
                    elapsed_days=excluded.elapsed_days,
                    review=excluded.review,
                    state=excluded.state,
                    reps=excluded.reps,
                    lapses=excluded.lapses
                """,
                (
                    user_id,
                    card_id,
                    review_log.stability,
                    review_log.difficulty,
                    review_log.rating.value,
                    review_log.scheduled_days,
                    review_log.elapsed_days,
                    review_log.review.isoformat(),
                    review_log.state.value,
                    review_log.reps,
                    review_log.lapses,
                ),
            )
            conn.commit()
