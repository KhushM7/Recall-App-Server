from datetime import datetime

from Flashcard_System.flashcard_model import (
    get_db_connection,
    get_flashcard,
    update_flashcard,
)
from fsrs import FSRS, Parameters


def get_user_rating():
    while True:
        rating = input("Rate the flashcard (1 = Again, 2 = Hard, 3 = Good, 4 = Easy): ")
        if rating in {"1", "2", "3", "4"}:
            return int(rating)
        else:
            print("Invalid rating. Please enter a number between 1 and 4.")


def main():
    user_id = 1
    flashcard_id = 1

    while flashcard_id <= 10:
        card = get_flashcard(flashcard_id)
        if card is None:
            print(f"Flashcard ID {flashcard_id} not found.")
            continue

        print(f"Question: {card.question}")
        input("Press Enter to flip the card...")
        print(f"Answer: {card.answer}")

        rating = get_user_rating()

        params = Parameters()
        fsrs = FSRS(params)

        updated_card = fsrs.review_card(card, rating)

        update_flashcard(updated_card)

        next_review_date = updated_card.due
        log_performance(flashcard_id, user_id, rating, next_review_date)

        print(f"Updated Flashcard:")
        print(f"Stability: {updated_card.stability}")
        print(f"Difficulty: {updated_card.difficulty}")
        print(f"Next Review Date: {next_review_date}")

        input("Press Enter to review the next flashcard...")
        flashcard_id += 1


def log_performance(
    flashcard_id: int,
    user_id: int,
    average_rating: int,
    last_rating: int,
    next_review: datetime,
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO UserPerformance (flashcard_id, user_id, average_rating, last_rating, response_time, next_review)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            flashcard_id,
            user_id,
            average_rating,
            last_rating,
            0.0,
            next_review.isoformat(),
        ),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
