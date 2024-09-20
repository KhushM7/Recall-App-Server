import math
from datetime import timedelta, datetime, timezone
from typing import Optional, Dict, Tuple


class Parameters:
    def __init__(self, request_retention: float = 0.9, maximum_interval: int = 36500):
        if not (0 < request_retention <= 1):
            raise ValueError("Retention must be between 0 and 1.")
        if maximum_interval <= 0:
            raise ValueError("Maximum interval must be greater than 0.")

        self.request_retention = request_retention
        self.maximum_interval = maximum_interval
        self.w = (
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
        )


class Card:
    def __init__(
        self,
        flashcard_id: str,
        set_name: str,
        question: str,
        answer: str,
        stability: float = 1.0,
        difficulty: float = 1.0,
        last_review: Optional[datetime] = None,
        reps: int = 0,
        state: str = "New",
    ):
        if stability < 0 or difficulty < 0:
            raise ValueError("Stability and difficulty must be non-negative.")
        self.flashcard_id = flashcard_id
        self.set_name = set_name
        self.question = question
        self.answer = answer
        self.stability = stability
        self.difficulty = difficulty
        self.last_review = last_review if last_review else datetime.now(timezone.utc)
        self.reps = reps
        self.state = state
        self.state_history = []  # Stack for managing transitions
        self.elapsed_days = 0
        self.due = self.last_review

    def update_review(self, new_state: str):
        """Update card state and push old state to history."""
        self.state_history.append(self.state)
        self.state = new_state


class FSRS:
    def __init__(self, parameters: Parameters):
        self.p = parameters
        self.DECAY = -0.5
        self.FACTOR = 0.9 ** (1 / self.DECAY) - 1
        self.memo: Dict[Tuple[float, int], float] = (
            {}
        )  # Memoization for calculated values

    def review_card(
        self, card: Card, rating: int, now: Optional[datetime] = None
    ) -> Card:
        if now is None:
            now = datetime.now(timezone.utc)
        card.elapsed_days = (now - card.last_review).days
        card.last_review = now
        card.reps += 1

        if card.state == "New":
            card.stability = self.init_stability(rating)
            card.difficulty = self.init_difficulty(rating)
            card.update_review("Learning")
            card.due = self.set_due_date(now, card)

        elif card.state == "Learning":
            card.stability = self.short_term_stability(card.stability, rating)
            card.difficulty = self.next_difficulty(card.difficulty, rating)
            if rating >= 3:
                card.update_review("Review")
            card.due = self.set_due_date(now, card)

        elif card.state == "Review":
            retrievability = self.forgetting_curve(card.elapsed_days, card.stability)
            card.stability = self.next_recall_stability(
                card.difficulty, card.stability, retrievability, rating
            )
            card.difficulty = self.next_difficulty(card.difficulty, rating)
            card.due = self.set_due_date(now, card)

        print(
            f"After review: Stability={card.stability:.4f}, Difficulty={card.difficulty:.4f}, Due={card.due}"
        )
        print(f"Rating: {rating}, Elapsed days: {card.elapsed_days}")
        return card

    def set_due_date(self, now: datetime, card: Card) -> datetime.date:
        """Set due date for the card based on the rating and current stability."""
        interval = self.next_interval(card.stability)
        return now.date() + timedelta(days=interval)

    def init_stability(self, rating: int) -> float:
        return max(self.p.w[rating - 1], 0.1)

    def init_difficulty(self, rating: int) -> float:
        return min(max(self.p.w[4] - math.exp(self.p.w[5] * (rating - 1)) + 1, 1), 10)

    def forgetting_curve(self, elapsed_days: int, stability: float) -> float:
        return (1 + self.FACTOR * elapsed_days / stability) ** self.DECAY

    def next_interval(self, s: float) -> int:
        new_interval = (
            s / self.FACTOR * (self.p.request_retention ** (1 / self.DECAY) - 1)
        )
        return min(max(round(new_interval), 1), self.p.maximum_interval)

    def next_difficulty(self, difficulty: float, rating: int) -> float:
        next_d = difficulty - self.p.w[6] * (rating - 3)
        return min(max(self.mean_reversion(self.init_difficulty(4), next_d), 1), 10)

    def short_term_stability(self, stability: float, rating: int) -> float:
        """Calculate short-term stability during the 'Learning' state."""
        return stability * math.exp(self.p.w[17] * (rating - 3 + self.p.w[18]))

    def mean_reversion(self, init: float, current: float) -> float:
        return self.p.w[7] * init + (1 - self.p.w[7]) * current

    def next_recall_stability(
        self, difficulty: float, stability: float, retrievability: float, rating: int
    ) -> float:
        """Calculate the next stability based on recall after review."""
        hard_penalty = self.p.w[15] if rating == 2 else 1
        easy_bonus = self.p.w[16] if rating == 4 else 1
        return stability * (
            1
            + math.exp(self.p.w[8])
            * (11 - difficulty)
            * math.pow(stability, -self.p.w[9])
            * (math.exp((1 - retrievability) * self.p.w[10]) - 1)
            * hard_penalty
            * easy_bonus
        )

    def next_forget_stability(
        self, difficulty: float, stability: float, retrievability: float
    ) -> float:
        """Calculate the next stability if the card is forgotten."""
        return (
            self.p.w[11]
            * math.pow(difficulty, -self.p.w[12])
            * (math.pow(stability + 1, self.p.w[13]) - 1)
            * math.exp((1 - retrievability) * self.p.w[14])
        )
