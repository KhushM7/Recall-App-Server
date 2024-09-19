from datetime import datetime
from Flashcard_System.flashcard_model import (
    get_db_connection,
    get_flashcard,
    update_flashcard,
)
from fsrs import FSRS, Parameters


def get_user_rating() -> int:
    while True:
        rating = input(
            "Rate the flashcard (1 = Again, 2 = Hard, 3 = Good, 4 = Easy): "
        ).strip()
        if rating in {"1", "2", "3", "4"}:
            return int(rating)
        print("Invalid rating. Please enter a number between 1 and 4.")


def review_flashcard(card, fsrs, user_id: int):
    print(f"Question: {card.question}")
    input("Press Enter to flip the card...")
    print(f"Answer: {card.answer}")

    rating = get_user_rating()

    updated_card = fsrs.review_card(card, rating)
    update_flashcard(updated_card)

    next_review_date = updated_card.due

    log_performance(card.flashcard_id, user_id, rating, next_review_date)
    return updated_card


def log_performance(
    flashcard_id: int, user_id: int, rating: int, next_review: datetime
):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT average_rating, last_rating, COUNT(*)
            FROM UserPerformance
            WHERE flashcard_id = ? AND user_id = ?
        """,
            (flashcard_id, user_id),
        )
        row = cursor.fetchone()

        if row and row["COUNT(*)"] > 0:
            update_existing_performance(
                cursor, row, flashcard_id, user_id, rating, next_review
            )
        else:
            insert_new_performance(cursor, flashcard_id, user_id, rating, next_review)

        conn.commit()


def update_existing_performance(
    cursor, row, flashcard_id: int, user_id: int, rating: int, next_review: datetime
):
    previous_avg_rating = row["average_rating"]
    number_of_ratings = row["COUNT(*)"]

    new_avg_rating = (previous_avg_rating * number_of_ratings + rating) / (
        number_of_ratings + 1
    )

    cursor.execute(
        """
        UPDATE UserPerformance
        SET average_rating = ?, last_rating = ?, next_review = ?
        WHERE flashcard_id = ? AND user_id = ?
        """,
        (new_avg_rating, rating, next_review.isoformat(), flashcard_id, user_id),
    )


def insert_new_performance(
    cursor, flashcard_id: int, user_id: int, rating: int, next_review: datetime
):
    cursor.execute(
        """
        INSERT INTO UserPerformance (flashcard_id, user_id, average_rating, last_rating, response_time, next_review)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            flashcard_id,
            user_id,
            rating,  # Since it's the first rating, set average as rating
            rating,
            0.0,  # Placeholder for response_time
            next_review.isoformat(),
        ),
    )


def main():
    user_id = 1  # Assuming a single user for this test scenario
    flashcard_id = 1

    params = Parameters()
    fsrs = FSRS(params)

    # Loop through flashcards until you hit the limit (10 cards in this demo)
    while flashcard_id <= 10:
        card = get_flashcard(flashcard_id)

        if card is None:
            print(f"Flashcard ID {flashcard_id} not found.")
            flashcard_id += 1
            continue

        review_flashcard(card, fsrs, user_id)

        input("Press Enter to review the next flashcard...")
        flashcard_id += 1


main()
