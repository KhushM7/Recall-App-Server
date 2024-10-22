from fsrs import FSRS, Card, Rating, State
from models import ReviewLog
from flashcard_db_operations import DatabaseOperations
from datetime import datetime, timedelta

# Initialize FSRS scheduler and database operations
fsrs_scheduler = FSRS()
db_ops = DatabaseOperations(
    "../physics_revision_app.db"
)  # Update to your actual DB path


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


def load_card_state(card_data: dict, user_id: int) -> Card:
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


def store_card_state(
    card: Card, rating: Rating, review_log: ReviewLog, user_id: int
) -> None:
    """Store the card's state in the UserPerformance table."""
    next_review_date = card.due.date()
    print(
        f"Storing card state: Card ID {card.card_id}, State {card.state}, Reps {card.reps}, Lapses {card.lapses}"
    )

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


def review_flashcards(user_id: int, review_date: datetime):
    """Review all flashcards due for the given user on the selected review_date."""

    # Step 1: Fetch the user's daily review limit
    daily_limit = db_ops.fetch_daily_review_limit(user_id)

    # Step 2: Fetch how many cards the user has already reviewed today
    today = review_date.date().isoformat()
    reviewed_today = db_ops.fetch_reviewed_today(user_id, today)

    # Step 3: Calculate remaining reviews allowed today
    remaining_reviews = max(0, daily_limit - reviewed_today)

    if remaining_reviews <= 0:
        print("You've reached your daily review limit. Come back tomorrow!")
        return

    # Step 4: Mark any unreviewed cards from previous days as priority and push next review to the next day
    db_ops.mark_cards_as_priority(user_id, today)

    # Step 5: Fetch due flashcards, limiting to the remaining reviews allowed
    flashcards = db_ops.fetch_due_cards(user_id, today, limit=remaining_reviews)

    if not flashcards:
        print("No flashcards found for this date!")
        return

    for card_data in flashcards:
        print(f"\nFlashcard: {card_data['front']} -> {card_data['back']}")

        # Load the current state of the card from the database
        card = load_card_state(card_data, user_id)

        # Ask user for a rating for the review
        rating = ask_user_for_rating()

        # Review the card using FSRS
        card, review_log = fsrs_scheduler.review_card(card, rating)

        # Store the updated card state in the UserPerformance table
        store_card_state(card, rating, review_log, user_id)

        # Step 6: After each review, increment the count of reviewed cards today
        db_ops.increment_reviewed_card_count(user_id, today)

    print(
        "\nBatch review completed. You can now check your UserPerformance table for analysis."
    )

    # Step 7: Mark any remaining unreviewed cards due today as priority and push next review to tomorrow
    db_ops.mark_today_unreviewed_as_priority(user_id, today)


def create_flashcard(user_id: int):
    """Prompt the user to create a new flashcard and save it to the database."""
    set_name = input("Enter the flashcard set name: ").strip()
    front = input("Enter the flashcard front: ").strip()
    back = input("Enter the flashcard back: ").strip()

    flashcard_data = {"set_name": set_name, "front": front, "back": back}

    db_ops.create_flashcard(user_id, flashcard_data)
    print(f"Flashcard created for user {user_id}: {front} -> {back}")


def main():
    print("Select User:")
    user_id = int(input("Enter User ID: ").strip())

    while True:
        print("\nSelect an option:")
        print("1: Review flashcards due today")
        print("2: Create new flashcards")
        print("3: Exit")

        option = input("Enter your option (1-3): ").strip()

        if option == "1":
            # For testing purposes, allow the user to set the date
            review_date_str = input(
                "Enter the review date (YYYY-MM-DD) or press Enter for today: "
            ).strip()
            if review_date_str:
                review_date = datetime.strptime(review_date_str, "%Y-%m-%d")
            else:
                review_date = datetime.now()

            review_flashcards(user_id, review_date)

        elif option == "2":
            create_flashcard(user_id)

        elif option == "3":
            print("Exiting...")
            break

        else:
            print("Invalid option! Please try again.")


if __name__ == "__main__":
    main()
    db_ops.close()

# Great. Thank you so much. The last feature to implement is to avoid Card Clumping. Can you explain to me the problem, generate a detailed plan to solve this. Then we will proceed to code this last feature.
