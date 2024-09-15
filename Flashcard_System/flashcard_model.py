import sqlite3
from datetime import datetime

from fsrs import Card


# Connect to the SQLite database
def get_db_connection():
    try:
        conn = sqlite3.connect("../physics_revision_app.db")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(e)


# Fetch a flashcard from the database
def get_flashcard(flashcard_id: int) -> Card:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT flashcard_id, set_name, question, answer, stability, ease, difficulty, last_review FROM Flashcards WHERE flashcard_id = ?",
        (flashcard_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    (
        flashcard_id,
        set_name,
        question,
        answer,
        stability,
        ease,
        difficulty,
        last_review_str,
    ) = row
    last_review = datetime.fromisoformat(last_review_str) if last_review_str else None
    return Card(
        flashcard_id,
        set_name,
        question,
        answer,
        stability,
        ease,
        difficulty,
        last_review,
    )


# Update a flashcard's review details
def update_flashcard(card: Card):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Flashcards
        SET stability = ?, ease = ?, difficulty = ?, last_review = ?, reps = ?
        WHERE flashcard_id = ?
    """,
        (
            card.stability,
            card.ease,
            card.difficulty,
            card.last_review.isoformat(),
            card.reps,
            card.flashcard_id,
        ),
    )
    conn.commit()
    conn.close()
