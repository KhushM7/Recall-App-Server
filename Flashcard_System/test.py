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
    # Replace with actual user ID
    user_id = 1
    flashcard_id = 1

    while flashcard_id <= 10:
        # Fetch the flashcard
        card = get_flashcard(flashcard_id)
        if card is None:
            print(f"Flashcard ID {flashcard_id} not found.")
            continue

        print(f"Question: {card.question}")
        input("Press Enter to flip the card...")
        print(f"Answer: {card.answer}")

        # Get the user's rating
        rating = get_user_rating()

        # Initialize FSRS parameters and scheduler
        params = Parameters()
        fsrs = FSRS(params)

        # Review the card
        updated_card = fsrs.review_card(card, rating)

        # Update the flashcard in the database
        update_flashcard(updated_card)

        # Log the review performance
        next_review_date = updated_card.due
        log_performance(flashcard_id, user_id, rating, next_review_date)

        print(f"Updated Flashcard:")
        print(f"Stability: {updated_card.stability}")
        print(f"Ease: {updated_card.ease}")
        print(f"Difficulty: {updated_card.difficulty}")
        print(f"Next Review Date: {next_review_date}")

        input("Press Enter to review the next flashcard...")
        flashcard_id += 1


def log_performance(
    flashcard_id: int, user_id: int, rating: int, next_review: datetime
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO UserPerformance (flashcard_id, user_id, rating, response_time, next_review)
        VALUES (?, ?, ?, ?, ?)
    """,
        (flashcard_id, user_id, rating, 0.0, next_review.isoformat()),
    )  # response_time is 0.0 for simplicity
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
