import sqlite3
from datetime import datetime, timezone

from fsrs import Card


def get_db_connection():
    try:
        conn = sqlite3.connect("../physics_revision_app.db")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(e)


def get_flashcard(flashcard_id: int) -> Card:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT flashcard_id, set_name, question, answer, stability, difficulty, last_review 
        FROM Flashcards 
        WHERE flashcard_id = ?
    """
    cursor.execute(query, (flashcard_id,))
    row = cursor.fetchone()
    conn.close()
    (
        flashcard_id,
        set_name,
        question,
        answer,
        stability,
        difficulty,
        last_review_str,
    ) = row
    last_review = (
        datetime.fromisoformat(last_review_str).replace(tzinfo=timezone.utc)
        if last_review_str
        else None
    )
    return Card(
        flashcard_id,
        set_name,
        question,
        answer,
        stability,
        difficulty,
        last_review,
    )


def update_flashcard(card: Card):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Flashcards
        SET stability = ?, difficulty = ?, last_review = ?, reps = ?
        WHERE flashcard_id = ?
    """,
        (
            card.stability,
            card.difficulty,
            card.last_review.isoformat(),
            card.reps,
            card.flashcard_id,
        ),
    )
    conn.commit()
    conn.close()
