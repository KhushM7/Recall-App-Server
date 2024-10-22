from Flashcard_System.flashcard_db_operations import DatabaseOperations
from Flashcard_System.flashcard_models import Card, Rating, ReviewLog
from Flashcard_System.b import FSRS


def get_user_rating() -> int:
    while True:
        rating = input(
            "Rate the flashcard (1 = Again, 2 = Hard, 3 = Good, 4 = Easy): "
        ).strip()
        if rating in {"1", "2", "3", "4"}:
            return int(rating)
        print("Invalid rating. Please enter a number between 1 and 4.")


def review_flashcard(card: Card, fsrs: FSRS, user_id: int):
    print(f"Question: {card.front}")
    input("Press Enter to flip the card...")
    print(f"Answer: {card.back}")

    rating = get_user_rating()
    updated_card, review_log = fsrs.review_card(card, Rating(rating))

    log_performance(user_id, updated_card, review_log)
    return updated_card


def log_performance(user_id: int, card: Card, review_log: ReviewLog):
    db_operations = DatabaseOperations("../physics_revision_app.db")
    db_operations.save_review_log(user_id, card.card_id, review_log)


def main():
    user_id = 1  # Assuming a single user for this test scenario
    db_operations = DatabaseOperations("../physics_revision_app.db")
    fsrs = FSRS(db_operations)

    # Loop through flashcards until you hit the limit (10 cards in this demo)
    for card_id in range(1, 11):
        card = db_operations.get_flashcard(card_id)

        if card is None:
            print(f"Flashcard ID {card_id} not found.")
            continue

        review_flashcard(card, fsrs, user_id)
        input("Press Enter to review the next flashcard...")


if __name__ == "__main__":
    main()
