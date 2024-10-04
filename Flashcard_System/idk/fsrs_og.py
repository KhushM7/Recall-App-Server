import math
from datetime import timedelta, datetime, timezone
from typing import Optional


class Parameters:
    def __init__(self, request_retention=0.9, maximum_interval=36500):
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
        flashcard_id,
        set_name,
        question,
        answer,
        stability=1.0,
        difficulty=1.0,
        last_review: Optional[datetime] = None,
        reps=0,
        state="New",  # Default state is 'New'
    ):
        self.flashcard_id = flashcard_id
        self.set_name = set_name
        self.question = question
        self.answer = answer
        self.stability = stability
        self.difficulty = difficulty
        self.last_review = last_review if last_review else datetime.now(timezone.utc)
        self.reps = 0
        self.elapsed_days = 0
        self.due = self.last_review
        self.reps = reps
        self.state = state


class FSRS:
    def __init__(self, parameters: Parameters):
        self.p = parameters
        self.DECAY = -0.5
        self.FACTOR = 0.9 ** (1 / self.DECAY) - 1

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
        print("State: ", card.state)

        if card.state == "New":
            # For new cards, initiate stability and difficulty based on the first rating
            card.stability = self.init_stability(rating)
            card.difficulty = self.init_difficulty(rating)
            if rating == 1:  # Again
                card.due = now.date()
            elif rating == 2:  # Hard
                card.due = now.date()
            elif rating == 3:  # Good
                card.due = now.date()
            elif rating == 4:  # Easy
                card.due = now.date() + timedelta(
                    days=self.next_interval(card.stability)
                )
            card.state = "Learning"  # Transition to Learning state after first review

        elif card.state == "Learning":
            # Handle short-term stability adjustments for Learning state
            if rating == 1:  # Again
                card.due = now.date()
            else:
                card.stability = self.next_stability(card.stability, rating)
                card.difficulty = self.next_difficulty(card.difficulty, rating)
                print(f"State: {card.state} Days: ", self.next_interval(card.stability))
                card.due = now.date() + timedelta(
                    days=self.next_interval(card.stability)
                )
            if rating >= 3:
                card.state = "Review"  # Move to Review state after a successful review

        elif card.state == "Review":
            # Regular interval updates for Review state
            card.stability = self.next_stability(card.stability, rating)
            card.difficulty = self.next_difficulty(card.difficulty, rating)
            print(f"State: {card.state} Days: ", self.next_interval(card.stability))
            card.due = now.date() + timedelta(days=self.next_interval(card.stability))

        return card

    def init_stability(self, rating: int) -> float:
        return max(self.p.w[rating - 1], 0.1)

    def init_difficulty(self, rating: int) -> float:
        return min(max(self.p.w[4] - math.exp(self.p.w[5] * (rating - 1)) + 1, 1), 10)

    def next_stability(self, stability: float, rating: int) -> float:
        return stability * math.exp(self.p.w[17] * (rating - 3 + self.p.w[18]))

    def next_difficulty(self, difficulty: float, rating: int) -> float:
        next_d = difficulty - self.p.w[6] * (rating - 3)
        return min(max(self.mean_reversion(self.init_difficulty(4), next_d), 1), 10)

    def next_interval(self, stability: float) -> int:
        new_interval = (
            stability / self.FACTOR * (self.p.request_retention ** (1 / self.DECAY) - 1)
        )
        return min(max(round(new_interval), 1), self.p.maximum_interval)

    def mean_reversion(self, init: float, current: float) -> float:
        return self.p.w[7] * init + (1 - self.p.w[7]) * current

    def forgetting_curve(self, elapsed_days: int, stability: float) -> float:
        return (1 + self.FACTOR * elapsed_days / stability) ** self.DECAY

    def short_term_stability(self, stability: float, rating: int) -> float:
        return stability * math.exp(self.p.w[17] * (rating - 3 + self.p.w[18]))

    def next_recall_stability(
        self, difficulty: float, stability: float, retrievability: float, rating: int
    ) -> float:
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
        return (
            self.p.w[11]
            * math.pow(difficulty, -self.p.w[12])
            * (math.pow(stability + 1, self.p.w[13]) - 1)
            * math.exp((1 - retrievability) * self.p.w[14])
        )
