import sqlite3
from datetime import datetime, timezone

from fsrs import Card


def get_db_connection():
    try:
        connection = sqlite3.connect("../../physics_revision_app.db")
        # detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        # Enable automatic type conversion between SQLite and Python for specific types.
        # PARSE_DECLTYPES: Converts declared column types (e.g., DATE, DATETIME) to Python types.
        # PARSE_COLNAMES: Allows type hints in column names (e.g., "created_at [timestamp]") to be parsed.
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as e:
        print(f"Database connection failed: {e}")
        return None


def fetch_flashcard_data(cursor, flashcard_id: int):
    """
    Fetches flashcard data from the database and returns it as a dictionary.
    """
    query = """
        SELECT flashcard_id, set_name, question, answer, stability, difficulty, last_review, reps, state
        FROM Flashcards 
        WHERE flashcard_id = ?
    """
    cursor.execute(query, (flashcard_id,))
    return cursor.fetchone()


def parse_flashcard_row(row):
    """
    Parses a database row into a Card object.
    """
    if not row:
        return None

    last_review_str = row["last_review"]
    last_review = (
        datetime.fromisoformat(last_review_str).replace(tzinfo=timezone.utc)
        if last_review_str
        else None
    )

    return Card(
        flashcard_id=row["flashcard_id"],
        set_name=row["set_name"],
        question=row["question"],
        answer=row["answer"],
        stability=row["stability"],
        difficulty=row["difficulty"],
        last_review=last_review,
        reps=row["reps"],
        state=row["state"],
    )


def get_flashcard(flashcard_id: int) -> Card | None:
    """
    Retrieves a flashcard from the database and converts it into a Card object.
    """
    with get_db_connection() as connection:
        if connection is None:
            return None
        cursor = connection.cursor()
        row = fetch_flashcard_data(cursor, flashcard_id)
        return parse_flashcard_row(row)


def update_flashcard(card: Card):
    """
    Updates a flashcard's data in the database based on the Card object provided.
    """
    try:
        with get_db_connection() as connection:
            if connection is None:
                return

            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE Flashcards
                SET stability = ?, difficulty = ?, last_review = ?, reps = ? , state = ?
                WHERE flashcard_id = ?
                """,
                (
                    card.stability,
                    card.difficulty,
                    card.last_review.date().isoformat(),
                    card.reps,
                    card.state,
                    card.flashcard_id,
                ),
            )
            connection.commit()
    except sqlite3.Error as e:
        print(f"Failed to update flashcard: {e}")
