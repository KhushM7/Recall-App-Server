import logging
from datetime import datetime, timezone
from typing import Any, Optional

from Flashcard_System.models.enums import State

# Configure logging
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Card:
    """
    Represents a flashcard in the FSRS system.

    Attributes:
        due (datetime): The date and time when the card is due next.
        stability (float): Core FSRS parameter used for scheduling.
        difficulty (float): Core FSRS parameter used for scheduling.
        elapsed_days (int): The number of days since the card was last reviewed.
        scheduled_days (int): The number of days until the card is due next.
        reps (int): The number of times the card has been reviewed in its history.
        lapses (int): The number of times the card has been lapsed in its history.
        state (State): The card's current learning state.
        last_review (datetime): The date and time of the card's last review.
    """

    def __init__(
        self,
        card_id: int,
        due: Optional[datetime] = None,
        stability: float = 0,
        difficulty: float = 0,
        elapsed_days: int = 0,
        scheduled_days: int = 0,
        reps: int = 0,
        lapses: int = 0,
        state: State = State.New,
        last_review: Optional[datetime] = None,
    ) -> None:
        """
        Creates and initializes a Card object.

        Note that each of the arguments for this method are optional and can be omitted when creating a new Card.

        Args:
            due (Optional[datetime]): The date and time when the card is due next.
            stability (float): Core FSRS parameter used for scheduling.
            difficulty (float): Core FSRS parameter used for scheduling.
            elapsed_days (int): The number of days since the card was last reviewed.
            scheduled_days (int): The number of days until the card is due next.
            reps (int): The number of times the card has been reviewed in its history.
            lapses (int): The number of times the card has been lapsed in its history.
            state (State): The card's current learning state.
            last_review (Optional[datetime]): The date and time of the card's last review.
        """
        self.card_id = card_id
        self.due = due if due else datetime.now(timezone.utc)

        self.stability = stability
        self.difficulty = difficulty
        self.elapsed_days = elapsed_days
        self.scheduled_days = scheduled_days
        self.reps = reps
        self.lapses = lapses
        self.state = state
        self.last_review = last_review

        logger.info("Initialized Card with ID %d.", self.card_id)

    def to_dict(self) -> dict[str, Any]:
        """
        Returns a JSON-serializable dictionary representation of the Card object.
        """
        logger.info("Converting Card %d to dictionary.", self.card_id)
        return_dict = {
            "card_id": self.card_id,
            "due": self.due.isoformat(),
            "stability": self.stability,
            "difficulty": self.difficulty,
            "elapsed_days": self.elapsed_days,
            "scheduled_days": self.scheduled_days,
            "reps": self.reps,
            "lapses": self.lapses,
            "state": self.state.value,
        }

        if hasattr(self, "last_review"):
            return_dict["last_review"] = self.last_review.isoformat()

        return return_dict

    @staticmethod
    def from_dict(source_dict: dict[str, Any]) -> "Card":
        """
        Creates a Card object from an existing dictionary.

        Args:
            source_dict (dict[str, Any]): A dictionary representing an existing Card object.

        Returns:
            Card: A Card object created from the provided dictionary.
        """
        try:
            card_id = int(source_dict.get("card_id", 0))
            due = datetime.fromisoformat(source_dict["due"])
            stability = float(source_dict["stability"])
            difficulty = float(source_dict["difficulty"])
            elapsed_days = int(source_dict["elapsed_days"])
            scheduled_days = int(source_dict["scheduled_days"])
            reps = int(source_dict["reps"])
            lapses = int(source_dict["lapses"])
            state = State(int(source_dict["state"]))
            last_review = (
                datetime.fromisoformat(source_dict["last_review"])
                if "last_review" in source_dict
                else None
            )
            logger.info(
                "Card successfully created from dictionary with ID: %d", card_id
            )
        except (KeyError, ValueError) as e:
            logger.error("Error parsing Card from dict: %s", e)
            raise ValueError(f"Error parsing Card from dict: {e}")

        return Card(
            card_id=card_id,
            due=due,
            stability=stability,
            difficulty=difficulty,
            elapsed_days=elapsed_days,
            scheduled_days=scheduled_days,
            reps=reps,
            lapses=lapses,
            state=state,
            last_review=last_review,
        )

    def get_retrievability(self, now: Optional[datetime] = None) -> float:
        """
        Calculates the Card object's current retrievability for a given date and time.

        Args:
            now (datetime): The current date and time

        Returns:
            float: The retrievability of the Card object.
        """
        DECAY = -0.5
        FACTOR = 0.9 ** (1 / DECAY) - 1

        if now is None:
            now = datetime.now(timezone.utc)

        if self.state in (State.Learning, State.Review, State.Relearning):
            elapsed_days = max(0, (now - self.last_review).days)
            retrievability = (1 + FACTOR * elapsed_days / self.stability) ** DECAY
            logger.info(
                "Retrievability for Card %d calculated: %f.",
                self.card_id,
                retrievability,
            )
            return retrievability
        else:
            logger.info(
                "Retrievability for Card %d is 0 due to inactive state.", self.card_id
            )
            return 0
