from typing import Optional, Tuple


class Parameters:
    """
    The parameters used to configure the FSRS scheduler.

    Attributes:
        request_retention (float): The desired retention of the scheduler. Corresponds to the maximum retrievability a Card object can have before it is due.
        maximum_interval (int): The maximum number of days into the future a Card object can be scheduled for next review.
        weights (tuple[float, ...]): The 19 model weights of the FSRS scheduler.
    """

    def __init__(
        self,
        weights: Optional[Tuple[float, ...]] = None,
        request_retention: Optional[float] = None,
        maximum_interval: Optional[int] = None,
    ) -> None:
        self.weights = (
            weights
            if weights is not None
            else (
                0.4072,
                1.1829,
                3.1262,
                15.4722,
                7.2102,
                0.5316,
                1.0651,
                0.0234,
                1.616,
                0.1544,
                1.0824,
                1.9813,
                0.0953,
                0.2975,
                2.2042,
                0.2407,
                2.9466,
                0.5034,
                0.6567,
            )
        )
        self.request_retention = (
            request_retention if request_retention is not None else 0.9
        )
        self.maximum_interval = (
            maximum_interval if maximum_interval is not None else 36500
        )
