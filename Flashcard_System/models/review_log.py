import logging
from datetime import datetime
from typing import Any, Union

from Flashcard_System.models.enums import Rating, State

# Configure logging (repeated for each file to ensure it's applied correctly)
logging.basicConfig(
    filename="../physics_server_log.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


class ReviewLog:
    """
    Represents the log entry of Card that has been reviewed.

    Attributes:
        rating (Rating): The rating given to the card during the review.
        scheduled_days (int): The number of days until the card is due next.
        elapsed_days (int): The number of days since the card was last reviewed.
        review (datetime): The date and time of the review.
        state (State): The learning state of the card before the review.
    """

    def __init__(
        self,
        rating: Rating,
        scheduled_days: int,
        elapsed_days: int,
        review: datetime,
        state: State,
    ) -> None:
        """
        Creates and initializes a ReviewLog object.

        Args:
            rating (Rating): The rating given to the card during the review.
            scheduled_days (int): The number of days until the card is due next.
            elapsed_days (int): The number of days since the card was last reviewed.
            review (datetime): The date and time of the review.
            state (State): The learning state of the card before the review.
        """
        self.rating = rating
        self.scheduled_days = scheduled_days
        self.elapsed_days = elapsed_days
        self.review = review
        self.state = state
        logging.info(f"ReviewLog created with rating {self.rating}.")

    def to_dict(self) -> dict[str, Union[int, str]]:
        """
        Returns a JSON-serializable dictionary representation of the ReviewLog object.

        This method is specifically useful for storing ReviewLog objects in a database.

        Returns:
            dict: A dictionary representation of the ReviewLog object.
        """
        return {
            "rating": self.rating.value,
            "scheduled_days": self.scheduled_days,
            "elapsed_days": self.elapsed_days,
            "review": self.review.isoformat(),
            "state": self.state.value,
        }

    @staticmethod
    def from_dict(source_dict: dict[str, Any]) -> "ReviewLog":
        """
        Creates a ReviewLog object from an existing dictionary.

        Args:
            source_dict (dict[str, Any]): A dictionary representing an existing ReviewLog object.

        Returns:
            ReviewLog: A ReviewLog object created from the provided dictionary.
        """
        try:
            rating = Rating(int(source_dict["rating"]))
            scheduled_days = int(source_dict["scheduled_days"])
            elapsed_days = int(source_dict["elapsed_days"])
            review = datetime.fromisoformat(source_dict["review"])
            state = State(int(source_dict["state"]))
        except (KeyError, ValueError) as e:
            logging.error(f"Error parsing ReviewLog from dict: {e}")
            raise ValueError(f"Error parsing ReviewLog from dict: {e}")

        logging.info("ReviewLog created from dictionary.")
        return ReviewLog(rating, scheduled_days, elapsed_days, review, state)
