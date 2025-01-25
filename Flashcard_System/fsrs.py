import math
from datetime import datetime, timezone, timedelta, time
from typing import Optional, Dict
import copy
import logging

from Flashcard_System.models.card import Card
from Flashcard_System.models.enums import Rating, State
from Flashcard_System.models.parameters import Parameters
from Flashcard_System.models.review_log import ReviewLog
from Flashcard_System.models.scheduler import SchedulingInfo, SchedulingCards

# Configure logging
logging.basicConfig(
    filename="application.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class FSRS:
    """
    The FSRS scheduler.

    Enables the reviewing and future scheduling of cards according to the FSRS algorithm.

    Attributes:
        p (Parameters): Object for configuring the scheduler's model weights, desired retention and maximum interval.
        DECAY (float): Constant used to model the forgetting curve and compute the length of a Card's next interval after being repeated.
        FACTOR (float): Constant used to model the forgetting curve and compute the length of a Card's next interval after being repeated.
    """

    p: Parameters
    DECAY: float
    FACTOR: float

    def __init__(
        self,
        w: Optional[tuple[float, ...]] = None,
        request_retention: Optional[float] = None,
        maximum_interval: Optional[int] = None,
    ) -> None:
        """
        Initializes the FSRS scheduler.

        Args:
            w (Optional[tuple[float, ...]]): The 19 model weights of the FSRS scheduler.
            request_retention (Optional[float]): The desired retention of the scheduler.
            maximum_interval (Optional[int]): The maximum number of days into the future a Card object can be scheduled for next review.
        """
        self.p = Parameters(w, request_retention, maximum_interval)
        self.DECAY = -0.5
        self.FACTOR = 0.9 ** (1 / self.DECAY) - 1
        logger.info("FSRS scheduler initialized with parameters.")

    def review_card(
        self, card: Card, rating: Rating, now: Optional[datetime] = None
    ) -> tuple[Card, ReviewLog]:
        """
        Reviews a card for a given rating.

        Args:
            card (Card): The card being reviewed.
            rating (Rating): The chosen rating for the card being reviewed.
            now (Optional[datetime]): The date and time of the review.

        Returns:
            tuple: A tuple containing the updated, reviewed card and its corresponding review log.
        """
        if now is None:
            if hasattr(card, "due"):
                now = card.due

        logger.info(
            "Reviewing card with ID %d at %s, rating: %s",
            card.card_id,
            now,
            rating.name,
        )

        scheduling_cards = self.generate_scheduling_cards(card, now)
        card = scheduling_cards.get(rating).card
        review_log = scheduling_cards.get(rating).review_log

        self.schedule_next_review(card, now)

        logger.info(
            "Card %d reviewed successfully, next due date: %s", card.card_id, card.due
        )
        return card, review_log

    def schedule_next_review(self, card: Card, now: datetime) -> None:
        """
        Adjusts the card's next review time to midnight, handling edge cases
        where the review is scheduled for the same day.
        """
        next_review_day = card.due.date()
        card.due = datetime.combine(next_review_day, time(0, 0, 0), tzinfo=timezone.utc)

        if card.due.date() == now.date():
            next_review_day = now.date() + timedelta(days=1)
            card.due = datetime.combine(
                next_review_day, time(0, 0, 0), tzinfo=timezone.utc
            )

        logger.info("Next review for card %d scheduled for %s", card.card_id, card.due)

    def generate_scheduling_cards(
        self, card: Card, now: Optional[datetime] = None
    ) -> Dict[Rating, SchedulingInfo]:
        """
        Dynamically generates SchedulingInfo for a given card, factoring in its state
        and calculating intervals for different ratings (Again, Hard, Good, Easy).
        """
        if now is None:
            if hasattr(card, "due"):
                now = card.due

        card = copy.deepcopy(card)
        self.update_card_state(card, now)
        scheduling_cards = SchedulingCards(card)
        scheduling_cards.update_state(card.state)

        if card.state == State.New:
            self.initialize_scheduling_intervals(scheduling_cards, now)
        else:
            self.update_scheduling_intervals(scheduling_cards, card, now)

        logger.info(
            "Scheduling info generated for card %d in state %s",
            card.card_id,
            card.state.name,
        )
        return scheduling_cards.record_log(card, now)

    def update_card_state(self, card: Card, now: datetime) -> None:
        """
        Updates the card's elapsed days and review count based on its state and last review time.
        """
        if card.state == State.New:
            card.elapsed_days = 0
        else:
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            if card.last_review.tzinfo is None:
                card.last_review = card.last_review.replace(tzinfo=timezone.utc)
            card.elapsed_days = (now - card.last_review).days

        card.last_review = now
        card.reps += 1
        logger.info(
            "Card %d updated with %d repetitions, elapsed days: %d",
            card.card_id,
            card.reps,
            card.elapsed_days,
        )

    def initialize_scheduling_intervals(
        self, scheduling_cards: SchedulingCards, now: datetime
    ) -> None:
        """
        Initializes scheduling intervals for a new card, setting times for Again, Hard, Good, and Easy ratings.
        """
        self.initialize_difficulty_stability(scheduling_cards)
        scheduling_cards.again.due = now + timedelta(minutes=1)
        scheduling_cards.hard.due = now + timedelta(minutes=5)
        scheduling_cards.good.due = now + timedelta(minutes=10)
        easy_interval = self.calculate_next_interval(scheduling_cards.easy.stability)
        scheduling_cards.easy.scheduled_days = easy_interval
        scheduling_cards.easy.due = now + timedelta(days=easy_interval)

        logger.info("Scheduling intervals initialized for new card.")

    def initialize_difficulty_stability(
        self, scheduling_cards: SchedulingCards
    ) -> None:
        """
        Initialize difficulty and stability values for each rating category when the card is new.
        """
        scheduling_cards.again.difficulty = self.init_difficulty(Rating.Again)
        scheduling_cards.again.stability = self.init_stability(Rating.Again)
        scheduling_cards.hard.difficulty = self.init_difficulty(Rating.Hard)
        scheduling_cards.hard.stability = self.init_stability(Rating.Hard)
        scheduling_cards.good.difficulty = self.init_difficulty(Rating.Good)
        scheduling_cards.good.stability = self.init_stability(Rating.Good)
        scheduling_cards.easy.difficulty = self.init_difficulty(Rating.Easy)
        scheduling_cards.easy.stability = self.init_stability(Rating.Easy)

    def update_scheduling_intervals(
        self, scheduling_cards: SchedulingCards, card: Card, now: datetime
    ) -> None:
        """
        Updates scheduling intervals for an existing card based on its difficulty and stability.
        """
        interval = card.elapsed_days
        last_difficulty = card.difficulty
        last_stability = card.stability
        retrievability = self.calculate_forgetting_curve(interval, last_stability)

        self.calculate_next_difficulty_stability(
            scheduling_cards,
            last_difficulty,
            last_stability,
            retrievability,
            card.state,
        )

        if card.state == State.Learning or card.state == State.Relearning:
            self.schedule_learning_card(scheduling_cards, now)
        else:
            self.schedule_review_card(scheduling_cards, now)

        logger.info("Scheduling intervals updated for card %d", card.card_id)

    def schedule_learning_card(
        self, scheduling_cards: SchedulingCards, now: datetime
    ) -> None:
        """
        Schedules the intervals for a card in the Learning or Relearning state.
        """
        hard_interval = 0
        good_interval = self.calculate_next_interval(scheduling_cards.good.stability)
        easy_interval = max(
            self.calculate_next_interval(scheduling_cards.easy.stability),
            good_interval + 1,
        )
        scheduling_cards.schedule(now, hard_interval, good_interval, easy_interval)

    def schedule_review_card(
        self, scheduling_cards: SchedulingCards, now: datetime
    ) -> None:
        """
        Schedules the intervals for a card in the Review state.
        """
        hard_interval = self.calculate_next_interval(scheduling_cards.hard.stability)
        good_interval = self.calculate_next_interval(scheduling_cards.good.stability)
        hard_interval = min(hard_interval, good_interval)
        good_interval = max(good_interval, hard_interval + 1)
        easy_interval = max(
            self.calculate_next_interval(scheduling_cards.easy.stability),
            good_interval + 1,
        )
        scheduling_cards.schedule(now, hard_interval, good_interval, easy_interval)

    def calculate_next_difficulty_stability(
        self,
        scheduling_cards: SchedulingCards,
        last_difficulty: float,
        last_stability: float,
        retrievability: float,
        state: State,
    ) -> None:
        """
        Calculates the next difficulty and stability for the card based on its last state and rating.
        """
        scheduling_cards.again.difficulty = self.calculate_next_difficulty(
            last_difficulty, Rating.Again
        )
        scheduling_cards.hard.difficulty = self.calculate_next_difficulty(
            last_difficulty, Rating.Hard
        )
        scheduling_cards.good.difficulty = self.calculate_next_difficulty(
            last_difficulty, Rating.Good
        )
        scheduling_cards.easy.difficulty = self.calculate_next_difficulty(
            last_difficulty, Rating.Easy
        )

        if state == State.Learning or state == State.Relearning:
            scheduling_cards.again.stability = self.calculate_short_term_stability(
                last_stability, Rating.Again
            )
            scheduling_cards.hard.stability = self.calculate_short_term_stability(
                last_stability, Rating.Hard
            )
            scheduling_cards.good.stability = self.calculate_short_term_stability(
                last_stability, Rating.Good
            )
            scheduling_cards.easy.stability = self.calculate_short_term_stability(
                last_stability, Rating.Easy
            )
        else:
            scheduling_cards.again.stability = self.calculate_next_forget_stability(
                last_difficulty, last_stability, retrievability
            )
            scheduling_cards.hard.stability = self.calculate_next_recall_stability(
                last_difficulty, last_stability, retrievability, Rating.Hard
            )
            scheduling_cards.good.stability = self.calculate_next_recall_stability(
                last_difficulty, last_stability, retrievability, Rating.Good
            )
            scheduling_cards.easy.stability = self.calculate_next_recall_stability(
                last_difficulty, last_stability, retrievability, Rating.Easy
            )

    def init_stability(self, r: Rating) -> float:
        return max(self.p.w[r - 1], 0.1)

    def init_difficulty(self, r: Rating) -> float:
        return min(max(self.p.w[4] - math.exp(self.p.w[5] * (r - 1)) + 1, 1), 10)

    def calculate_forgetting_curve(self, elapsed_days: int, stability: float) -> float:
        return (1 + self.FACTOR * elapsed_days / stability) ** self.DECAY

    def calculate_next_interval(self, stability: float) -> int:
        new_interval = (
            stability / self.FACTOR * (self.p.request_retention ** (1 / self.DECAY) - 1)
        )
        return min(max(math.ceil(new_interval), 1), self.p.maximum_interval)

    def calculate_next_difficulty(
        self, current_difficulty: float, rating: Rating
    ) -> float:
        next_difficulty = current_difficulty - self.p.w[6] * (rating - 3)
        return min(
            max(
                self.mean_reversion(self.init_difficulty(Rating.Easy), next_difficulty),
                1,
            ),
            10,
        )

    def calculate_short_term_stability(self, stability: float, rating: Rating) -> float:
        return stability * math.exp(self.p.w[17] * (rating - 3 + self.p.w[18]))

    def mean_reversion(self, init: float, current: float) -> float:
        return self.p.w[7] * init + (1 - self.p.w[7]) * current

    def calculate_next_recall_stability(
        self, difficulty: float, stability: float, retrievability: float, rating: Rating
    ) -> float:
        hard_penalty = self.p.w[15] if rating == Rating.Hard else 1
        easy_bonus = self.p.w[16] if rating == Rating.Easy else 1
        return stability * (
            1
            + math.exp(self.p.w[8])
            * (11 - difficulty)
            * math.pow(stability, -self.p.w[9])
            * (math.exp((1 - retrievability) * self.p.w[10]) - 1)
            * hard_penalty
            * easy_bonus
        )

    def calculate_next_forget_stability(
        self, difficulty: float, stability: float, retrievability: float
    ) -> float:
        return (
            self.p.w[11]
            * math.pow(difficulty, -self.p.w[12])
            * (math.pow(stability + 1, self.p.w[13]) - 1)
            * math.exp((1 - retrievability) * self.p.w[14])
        )
