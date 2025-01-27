import random
from datetime import datetime, timedelta
import logging

from Flashcard_System.database_operations.database_service import DatabaseService
from Flashcard_System.fsrs import FSRS
from Flashcard_System.models.card import Card
from Flashcard_System.models.enums import Rating, State
from Flashcard_System.models.review_log import ReviewLog

# Configure logging
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class FSRSManager:
    def __init__(self, db_path: str):
        self.fsrs_scheduler = FSRS()
        self.db_service = DatabaseService(db_path)
        logger.info("FSRSManager initialized with database path: %s", db_path)

    def fetch_due_flashcards(self, user_id: int, review_date: datetime):
        """
        Fetch flashcards due for review for a specific user on a specific date.
        Enforces daily limits and marks cards as priority for the session.
        """
        try:
            daily_limit = self.db_service.user_settings_ops.fetch_daily_review_limit(
                user_id
            )
            if daily_limit is None:
                raise ValueError(f"No daily review limit set for user {user_id}")

            today = review_date.date().isoformat()
            reviewed_today = self.db_service.daily_review_log_ops.fetch_reviewed_today(
                user_id, today
            )
            remaining_reviews = max(0, daily_limit - reviewed_today)

            self.db_service.user_performance_ops.mark_cards_as_priority(user_id, today)

            flashcards = self.db_service.flashcard_ops.fetch_due_cards(
                user_id, today, limit=remaining_reviews
            )

            if not flashcards:
                logger.info("No flashcards found for user %d on %s", user_id, today)

            return flashcards

        except Exception as e:
            logger.error(
                "Error fetching due flashcards for user %d on %s: %s",
                user_id,
                review_date,
                e,
            )
            raise

    def process_rating(
        self, user_id: int, card_id: int, rating: str, review_date: datetime
    ):
        """
        Processes the given flashcard with the specified rating, adjusts stability and difficulty,
        applies delays if needed, and stores the updated state in the database.
        """
        try:
            today = review_date.date().isoformat()
            try:
                rating_enum = Rating[rating]
            except KeyError:
                logger.error("Invalid rating value: %s", rating)
                return False

            card_data = self.db_service.flashcard_ops.fetch_card_by_id(card_id)
            if not card_data:
                logger.error("Card with ID %d not found for user %d.", card_id, user_id)
                return False

            card = self._load_card_state(card_data, user_id)

            # Review the card using the FSRS scheduler with the enum rating
            card, review_log = self.fsrs_scheduler.review_card(card, rating_enum)

            # Check if the card has been reviewed on the same day to possibly apply a delay
            reviewed_same_day_data = self.db_service.user_performance_ops.fetch(
                """
                SELECT stability, difficulty
                FROM UserPerformance
                WHERE user_id = ? AND DATE(review_time) = ?
                """,
                (user_id, today),
            )
            reviewed_same_day = [
                (row["stability"], row["difficulty"]) for row in reviewed_same_day_data
            ]

            if (card.stability, card.difficulty) in reviewed_same_day:
                delay = random.randint(0, 1)  # Random delay of 0 or 1 day
                card.due += timedelta(days=delay)
                card.scheduled_days += delay
                logger.info(
                    "Random delay of %d day(s) applied to card %d", delay, card.card_id
                )

            self._store_card_state(card, rating_enum, review_log, user_id)

            self.db_service.daily_review_log_ops.increment_reviewed_card_count(
                user_id, today
            )
            self.db_service.user_performance_ops.mark_cards_as_priority(
                user_id, today, mark_today=True
            )
            logger.info(
                "Successfully processed rating for user %d, card %d", user_id, card_id
            )
            return True

        except Exception as e:
            logger.error(
                "Error processing rating for user %d, card %d: %s", user_id, card_id, e
            )
            raise

    def _load_card_state(self, card_data: dict, user_id: int) -> Card:
        """Load or initialize a card's state from the UserPerformance table."""
        try:
            performance_data = (
                self.db_service.user_performance_ops.fetch_user_performance(
                    user_id, card_data["card_id"]
                )
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
                logger.info("Loaded card state: Card ID %d", card.card_id)
            else:
                card = Card(card_id=card_data["card_id"])
                logger.info("New card initialized: Card ID %d", card.card_id)

            return card
        except Exception as e:
            logger.error(
                "Error loading card state for user %d, card %d: %s",
                user_id,
                card_data["card_id"],
                e,
            )
            raise

    def _store_card_state(
        self, card: Card, rating: Rating, review_log: ReviewLog, user_id: int
    ) -> None:
        """Store the updated card state in the UserPerformance table."""
        try:
            next_review_date = card.due.date()
            logger.info("Storing card state: Card ID %d", card.card_id)

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

            self.db_service.user_performance_ops.store_review_result(
                user_id, card_review_data
            )
            logger.info("Card state stored successfully: Card ID %d", card.card_id)
        except Exception as e:
            logger.error(
                "Error storing card state for user %d, card %d: %s",
                user_id,
                card.card_id,
                e,
            )
            raise

    def close(self):
        """Close the database service connection."""
        self.db_service.close()
        logger.info("Database service connection closed")
