import random

from Flashcard_System.database_operations.database_service import DatabaseService

from datetime import datetime, timedelta
import logging

from Flashcard_System.fsrs import FSRS
from Flashcard_System.models.card import Card
from Flashcard_System.models.enums import Rating, State
from Flashcard_System.models.review_log import ReviewLog

# Configure logging
logging.basicConfig(
    filename="../physics_server_log.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Initialize FSRS scheduler and database service
fsrs_scheduler = FSRS()
db_service = DatabaseService("../physics_revision_app.db")


def ask_user_for_rating() -> Rating:
    """Prompt the user for a rating and return the corresponding Rating enum."""
    try:
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
            logging.warning(
                f"Invalid rating input: {rating_input}, defaulting to 'Again'"
            )
            return Rating.Again
    except Exception as e:
        logging.error(f"Error asking user for rating: {e}")
        raise


def load_card_state(card_data: dict, user_id: int) -> Card:
    """Load the card's state from the UserPerformance table or create a new Card."""
    try:
        performance_data = db_service.user_performance_ops.fetch_user_performance(
            user_id, card_data["card_id"]
        )

        if performance_data:
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
            logging.info(
                f"Loaded card state: Card ID {card.card_id}, State {card.state}, Reps {card.reps}, Lapses {card.lapses}"
            )
        else:
            card = Card(card_id=card_data["card_id"])
            logging.info(
                f"New card created: Card ID {card.card_id}, Initial State {card.state}"
            )

        return card
    except Exception as e:
        logging.error(
            f"Error loading card state for user {user_id}, card {card_data['card_id']}: {e}"
        )
        raise


def store_card_state(
    card: Card, rating: Rating, review_log: ReviewLog, user_id: int
) -> None:
    """Store the card's state in the UserPerformance table."""
    try:
        next_review_date = card.due.date()
        logging.info(
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

        db_service.user_performance_ops.store_review_result(user_id, card_review_data)
    except Exception as e:
        logging.error(
            f"Error storing card state for user {user_id}, card {card.card_id}: {e}"
        )
        raise


def review_flashcards(user_id: int, review_date: datetime):
    """Review all flashcards due for the given user on the selected review_date."""
    try:
        daily_limit = db_service.user_settings_ops.fetch_daily_review_limit(user_id)
        if daily_limit is None:
            raise ValueError(f"No daily review limit set for user {user_id}")

        today = review_date.date().isoformat()
        reviewed_today = db_service.daily_review_log_ops.fetch_reviewed_today(
            user_id, today
        )

        remaining_reviews = max(0, daily_limit - reviewed_today)

        db_service.user_performance_ops.mark_cards_as_priority(user_id, today)

        flashcards = db_service.flashcard_ops.fetch_due_cards(
            user_id, today, limit=remaining_reviews
        )

        if not flashcards:
            logging.info("No flashcards found for this date!")
            return

        for card_data in flashcards:
            reviewed_same_day_query = """
                        SELECT stability, difficulty
                        FROM UserPerformance
                        WHERE user_id = ? AND DATE(review_time) = ?
                    """
            reviewed_same_day_data = db_service.user_performance_ops.fetch(
                reviewed_same_day_query, (user_id, today)
            )
            reviewed_same_day = [
                (row["stability"], row["difficulty"]) for row in reviewed_same_day_data
            ]
            print(f"\nFlashcard: {card_data['front']} -> {card_data['back']}")

            card = load_card_state(card_data, user_id)

            rating = ask_user_for_rating()

            card, review_log = fsrs_scheduler.review_card(card, rating)

            card_stability_difficulty = (card.stability, card.difficulty)
            logging.info(
                f"Current card stability: {card.stability}, difficulty: {card.difficulty}"
            )
            if card_stability_difficulty in reviewed_same_day:
                delay = random.randint(0, 1)  # Random delay of 0 or 1 day
                card.due = card.due + timedelta(days=delay)
                card.scheduled_days += delay
                logging.info(
                    f"Random delay of {delay} day(s) applied to card {card.card_id}"
                )

            store_card_state(card, rating, review_log, user_id)

            db_service.daily_review_log_ops.increment_reviewed_card_count(
                user_id, today
            )

        logging.info(
            "\nBatch review completed. You can now check your UserPerformance table for analysis."
        )

        db_service.user_performance_ops.mark_cards_as_priority(
            user_id, today, mark_today=True
        )
    except Exception as e:
        logging.error(f"Error during flashcard review process for user {user_id}: {e}")
        raise


def create_flashcard(user_id: int):
    """Prompt the user to create a new flashcard and save it to the database."""
    try:
        set_name = input("Enter the flashcard set name: ").strip()
        front = input("Enter the flashcard front: ").strip()
        back = input("Enter the flashcard back: ").strip()

        if not set_name or not front or not back:
            raise ValueError(
                "Set name, front, and back of the flashcard must not be empty."
            )

        flashcard_data = {"set_name": set_name, "front": front, "back": back}

        db_service.flashcard_ops.create_flashcard(user_id, flashcard_data)
        logging.info(f"Flashcard created for user {user_id}: {front} -> {back}")
    except Exception as e:
        logging.error(f"Error creating flashcard for user {user_id}: {e}")
        raise


def main():
    try:
        print("Select User:")
        user_id = int(input("Enter User ID: ").strip())

        while True:
            print("\nSelect an option:")
            print("1: Review flashcards due today")
            print("2: Create new flashcards")
            print("3: Exit")

            option = input("Enter your option (1-3): ").strip()

            if option == "1":
                review_date_str = input(
                    "Enter the review date (YYYY-MM-DD) or press Enter for today: "
                ).strip()
                review_date = (
                    datetime.strptime(review_date_str, "%Y-%m-%d")
                    if review_date_str
                    else datetime.now()
                )

                review_flashcards(user_id, review_date)

            elif option == "2":
                create_flashcard(user_id)

            elif option == "3":
                logging.info("Exiting...")
                break

            else:
                print("Invalid option! Please try again.")
    except Exception as e:
        logging.error(f"Error in main application loop: {e}")
        raise
    finally:
        db_service.close()


if __name__ == "__main__":
    main()
