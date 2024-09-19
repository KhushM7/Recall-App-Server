import math
from datetime import timedelta, datetime, timezone
from typing import Optional


class Parameters:
    def __init__(self, request_retention=0.9, maximum_interval=36500):
        self.request_retention = request_retention
        self.maximum_interval = maximum_interval
        self.weights = [
            0.4197,
            1.1869,
            3.0412,
            15.2441,
            7.1434,
            0.6477,
            1.0007,
            0.0674,
            1.6597,
            0.1712,
            1.1178,
            2.0225,
            0.0904,
            0.3025,
            2.1214,
            0.2498,
            2.9466,
            0.4891,
            0.6468,
        ]

        # Store commonly used values for a faster lookup
        self.precomputed_values = {
            "stability_factor": self.weights[17],
            "difficulty_factor": self.weights[6],
            "mean_reversion_factor": self.weights[7],
            "request_retention_factor": self.request_retention ** (-2),
        }


class Card:
    def __init__(
        self,
        flashcard_id,
        set_name,
        question,
        answer,
        stability=1.0,
        difficulty=1.0,
        last_review: Optional[datetime] = None,
        reps=0,
        state="New",
    ):
        self.flashcard_id = flashcard_id
        self.set_name = set_name
        self.question = question
        self.answer = answer
        self.stability = stability
        self.difficulty = difficulty
        self.last_review = last_review if last_review else datetime.now(timezone.utc)
        self.reps = reps
        self.elapsed_days = 0
        self.due = self.last_review
        self.state = state


class FSRS:
    def __init__(self, parameters: Parameters):
        self.p = parameters
        self.memoized_stability = {}  # Cache for memoization

    def review_card(
        self, card: Card, rating: int, now: Optional[datetime] = None
    ) -> Card:
        if now is None:
            now = datetime.now(timezone.utc)
        if card.last_review.tzinfo is None:
            card.last_review = card.last_review.replace(tzinfo=timezone.utc)

        card.elapsed_days = (now - card.last_review).days
        card.last_review = now
        card.reps += 1

        state_transitions = {
            "New": self.process_new_card,
            "Learning": self.process_learning_card,
            "Review": self.process_review_card,
        }

        state_transitions.get(card.state, lambda *args: None)(card, rating, now)
        return card

    def process_new_card(self, card: Card, rating: int, now: datetime):
        card.stability = self.init_stability(rating)
        card.difficulty = self.init_difficulty(rating)

        if rating == 4:
            card.due = now.date() + timedelta(days=self.next_interval(card.stability))
        else:
            card.due = now.date()

        card.state = "Learning" if rating > 1 else "New"

    def process_learning_card(self, card: Card, rating: int, now: datetime):
        if rating == 1:
            card.due = now.date()
        else:
            card.stability = self.next_stability(card.stability, rating)
            card.difficulty = self.next_difficulty(card.difficulty, rating)
            card.due = now.date() + timedelta(days=self.next_interval(card.stability))

        if rating >= 3:
            card.state = "Review"

    def process_review_card(self, card: Card, rating: int, now: datetime):
        card.stability = self.next_stability(card.stability, rating)
        card.difficulty = self.next_difficulty(card.difficulty, rating)
        card.due = now.date() + timedelta(days=self.next_interval(card.stability))

    def init_stability(self, rating: int) -> float:
        # Use a hash table for quick lookup
        return self.p.weights[rating - 1]

    def init_difficulty(self, rating: int) -> float:
        # Use list comprehensions for quick calculations
        return min(
            max(self.p.weights[4] - math.exp(self.p.weights[5] * (rating - 1)) + 1, 1),
            10,
        )

    def next_stability(self, stability: float, rating: int) -> float:
        # Check cache for previously computed stability
        if (stability, rating) in self.memoized_stability:
            return self.memoized_stability[(stability, rating)]

        # Calculate next stability using exponential formula and cache result
        new_stability = stability * math.exp(
            self.p.precomputed_values["stability_factor"]
            * (rating - 3 + self.p.weights[18])
        )
        self.memoized_stability[(stability, rating)] = new_stability
        return new_stability

    def next_difficulty(self, difficulty: float, rating: int) -> float:
        next_difficulty = difficulty - self.p.weights[6] * (rating - 3)
        return min(
            max(self.mean_reversion(self.init_difficulty(4), next_difficulty), 1), 10
        )

    def next_interval(self, stability: float) -> int:
        # Simulating advanced matrix operations with list comprehensions
        new_interval = stability * self.p.precomputed_values["request_retention_factor"]
        return min(max(round(new_interval), 1), self.p.maximum_interval)

    def mean_reversion(self, init: float, current: float) -> float:
        return (
            self.p.precomputed_values["mean_reversion_factor"] * init
            + (1 - self.p.precomputed_values["mean_reversion_factor"]) * current
        )

    def forgetting_curve(self, elapsed_days: int, stability: float) -> float:
        if elapsed_days == 0:
            return 1.0
        return (
            1
            + self.p.precomputed_values["request_retention_factor"]
            * elapsed_days
            / stability
        ) ** -2 * self.forgetting_curve(elapsed_days - 1, stability)

    def next_recall_stability(
        self, difficulty: float, stability: float, retrievability: float, rating: int
    ) -> float:
        if rating == 1:
            return stability
        return stability * (
            1
            + math.exp(self.p.weights[8])
            * (11 - difficulty)
            * math.pow(stability, -self.p.weights[9])
            * (math.exp((1 - retrievability) * self.p.weights[10]) - 1)
            * (self.p.weights[15] if rating == 2 else 1)  # Hard penalty
            * (self.p.weights[16] if rating == 4 else 1)  # Easy bonus
        )
