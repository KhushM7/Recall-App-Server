from fsrs import FSRS, Card, Rating, State
from models import ReviewLog
from flashcard_db_operations import DatabaseOperations
from datetime import datetime, timedelta

# Initialize FSRS scheduler and database operations
fsrs_scheduler = FSRS()
db_ops = DatabaseOperations(
    "../physics_revision_app.db"
)  # Replace with your actual database path
user_id = 1  # Assume we're testing for a single user with ID 1


def ask_user_for_rating() -> Rating:
    """Prompt the user for a rating and return the corresponding Rating enum."""
    print("\nHow would you rate your recall?")
    print("1: Again (forgot)")
    print("2: Hard (recalled with difficulty)")
    print("3: Good (recalled with hesitation)")
    print("4: Easy (perfect recall)")

    rating_input = input("Enter your rating (1-4): ").strip()
    if rating_input == "1":
        return Rating.Again
    elif rating_input == "2":
        return Rating.Hard
    elif rating_input == "3":
        return Rating.Good
    elif rating_input == "4":
        return Rating.Easy
    else:
        print("Invalid rating, defaulting to 'Again'")
        return Rating.Again


def load_card_state(card_data: dict) -> Card:
    """Load the card's state from the UserPerformance table or create a new Card."""
    performance_data = db_ops.fetch_user_performance(user_id, card_data["card_id"])

    if performance_data:
        # Card has been reviewed before; load its state
        card = Card(
            card_id=card_data["card_id"],
            due=datetime.fromisoformat(performance_data["next_review_date"]),
            stability=performance_data["stability"],
            difficulty=performance_data["difficulty"],
            elapsed_days=performance_data["elapsed_days"],
            scheduled_days=performance_data["scheduled_days"],
            reps=performance_data["reps"],
            lapses=performance_data["lapses"],
            state=State(performance_data["state"]),
            last_review=datetime.fromisoformat(performance_data["review_time"]),
        )
        print(
            f"Loaded card state: Card ID {card.card_id}, State {card.state}, Reps {card.reps}, Lapses {card.lapses}"
        )
    else:
        # New card, create with default state
        card = Card(card_id=card_data["card_id"])
        print(f"New card created: Card ID {card.card_id}, Initial State {card.state}")

    return card


def store_card_state(card: Card, rating: Rating, review_log: ReviewLog) -> None:
    """Store the card's state in the UserPerformance table."""
    next_review_date = card.due
    print(
        f"Storing card state: Card ID {card.card_id}, State {card.state}, Reps {card.reps}, Lapses {card.lapses}"
    )
    # Assuming `card` is an instance of the Card class
    # print(
    #     f"""
    # Card Attributes:
    #     CardID: {card.card_id},
    #     Due: {card.due},
    #     Stability: {card.stability},
    #     Difficulty: {card.difficulty},
    #     Elapsed Days: {card.elapsed_days},
    #     Scheduled Days: {card.scheduled_days},
    #     Reps: {card.reps},
    #     Lapses: {card.lapses},
    #     State: {card.state},
    #     Last Review: {card.last_review if hasattr(card, 'last_review') else 'N/A'}
    # """
    # )
    #
    # # Assuming `review_log` is an instance of the ReviewLog class
    # print(
    #     f"""
    # ReviewLog Attributes:
    #     Rating: {review_log.rating},
    #     Scheduled Days: {review_log.scheduled_days},
    #     Elapsed Days: {review_log.elapsed_days},
    #     Review: {review_log.review},
    #     State: {review_log.state}
    # """
    # )
    card_review_data = {
        "card_id": card.card_id,
        "rating": rating.value,
        "scheduled_days": review_log.scheduled_days,
        "elapsed_days": review_log.elapsed_days,
        "review_time": review_log.review,
        "state": card.state.value,
        "next_review_date": next_review_date,
        "stability": card.stability,
        "difficulty": card.difficulty,
        "reps": card.reps,
        "lapses": card.lapses,
    }

    db_ops.store_review_result(user_id, card_review_data)


def review_flashcards():
    """Review all flashcards in the batch and store results."""
    flashcards = db_ops.fetch_flashcards()

    if not flashcards:
        print("No flashcards found!")
        return

    for card_data in flashcards:
        print(f"\nFlashcard: {card_data['front']} -> {card_data['back']}")

        # Load the current state of the card from the database
        card = load_card_state(card_data)
        # print(f"""
        #                 UserID: {user_id},
        #                 CardID: {card.card_id},
        #                 Stability: {card.stability},
        #                 Difficulty: {card.difficulty},
        #                 Scheduled Days: {card.scheduled_days},
        #                 Elapsed Days: {card.elapsed_days},
        #                 Review: {card.last_review},
        #                 State: {card.state.value},
        #                 Reps: {card.reps},
        #                 Lapses: {card.lapses}
        #             """)
        # Ask user for a rating for the review
        rating = ask_user_for_rating()

        # Simulate correct review time
        # if hasattr(card, "last_review"):
        #     card.last_review = card.due
        #     print("LAST REVIEW: ", card.last_review)
        #     print("DUE: ", card.due)

        # Review the card using FSRS
        card, review_log = fsrs_scheduler.review_card(card, rating)

        # Store the updated card state in the UserPerformance table
        store_card_state(card, rating, review_log)

    print(
        "\nBatch review completed. You can now check your UserPerformance table for analysis."
    )


# Run the test
if __name__ == "__main__":
    review_flashcards()
    db_ops.close()
