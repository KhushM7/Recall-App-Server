import copy
import logging
from datetime import datetime, timedelta

from typing import Dict

from Flashcard_System.models.card import Card
from Flashcard_System.models.enums import State, Rating
from Flashcard_System.models.review_log import ReviewLog

# Configure logging
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SchedulingInfo:
    """
    Simple data class that bundles together an updated Card object, and its corresponding ReviewLog object.

    This class is specifically used to provide an updated card, and its review log after a card has been reviewed.
    """

    def __init__(self, card: Card, review_log: ReviewLog) -> None:
        self.card = card
        self.review_log = review_log


class SchedulingCards:
    """
    Manages the scheduling of a Card object for each of the four potential ratings.

    A SchedulingCards object is created from an existing card and creates four new potential cards which
    are updated according to whether the card will be chosen to be reviewed as Again, Hard, Good or Easy.

    Attributes:
        again (Card): An updated Card object that was rated Again.
        hard (Card): An updated Card object that was rated Hard.
        good (Card): An updated Card object that was rated Good.
        easy (Card): An updated Card object that was rated Easy.
    """

    def __init__(self, card: Card) -> None:
        self.again = copy.deepcopy(card)
        self.hard = copy.deepcopy(card)
        self.good = copy.deepcopy(card)
        self.easy = copy.deepcopy(card)
        logger.info("SchedulingCards initialized for Card %d.", card.card_id)

    def update_state(self, state: State) -> None:
        logger.info("Updating state for SchedulingCards. Original state: %s.", state)
        if state == State.New:
            self.again.state = State.Learning
            self.hard.state = State.Learning
            self.good.state = State.Learning
            self.easy.state = State.Review
        elif state == State.Learning or state == State.Relearning:
            self.again.state = state
            self.hard.state = state
            self.good.state = State.Review
            self.easy.state = State.Review
        elif state == State.Review:
            self.again.state = State.Relearning
            self.hard.state = State.Review
            self.good.state = State.Review
            self.easy.state = State.Review
            self.again.lapses += 1
        logger.info(
            "State updated for SchedulingCards: Again=%s, Hard=%s, Good=%s, Easy=%s.",
            self.again.state,
            self.hard.state,
            self.good.state,
            self.easy.state,
        )

    def schedule(
        self, now: datetime, hard_interval: int, good_interval: int, easy_interval: int
    ) -> None:
        """
        Schedules the review times for the different rating categories (Again, Hard, Good, Easy).
        """
        self.again.scheduled_days = 0
        self.again.due = now + timedelta(minutes=5)

        self.hard.scheduled_days = hard_interval
        self.hard.due = now + timedelta(
            minutes=10 if hard_interval == 0 else hard_interval
        )

        self.good.scheduled_days = good_interval
        self.good.due = now + timedelta(days=good_interval)

        self.easy.scheduled_days = easy_interval
        self.easy.due = now + timedelta(days=easy_interval)

        logger.info(
            "Scheduling complete for Card. Hard due in %d days, Good due in %d days, Easy due in %d days.",
            hard_interval,
            good_interval,
            easy_interval,
        )

    def record_log(self, card: Card, now: datetime) -> Dict[Rating, SchedulingInfo]:
        """
        Records the scheduling information and review log for each rating category.
        """
        logger.info(
            "Recording scheduling information and review logs for Card %d.",
            card.card_id,
        )
        return {
            Rating.Again: SchedulingInfo(
                self.again,
                ReviewLog(
                    Rating.Again,
                    self.again.scheduled_days,
                    card.elapsed_days,
                    now,
                    card.state,
                ),
            ),
            Rating.Hard: SchedulingInfo(
                self.hard,
                ReviewLog(
                    Rating.Hard,
                    self.hard.scheduled_days,
                    card.elapsed_days,
                    now,
                    card.state,
                ),
            ),
            Rating.Good: SchedulingInfo(
                self.good,
                ReviewLog(
                    Rating.Good,
                    self.good.scheduled_days,
                    card.elapsed_days,
                    now,
                    card.state,
                ),
            ),
            Rating.Easy: SchedulingInfo(
                self.easy,
                ReviewLog(
                    Rating.Easy,
                    self.easy.scheduled_days,
                    card.elapsed_days,
                    now,
                    card.state,
                ),
            ),
        }
