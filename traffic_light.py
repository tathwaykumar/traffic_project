"""
traffic_light.py  —  Traffic signal controller
------------------------------------------------
Each of the four lanes has one TrafficLight that knows its state,
how long it has been green, and how to compute smart green durations.
"""


class TrafficLight:
    """
    Controls one lane's signal at the intersection.

    States : 'red' | 'green'
    Modes  : Fixed 10 s (Normal) or proportional (Smart, 5–20 s)
    """

    DEFAULT_GREEN_DURATION = 10.0   # Normal mode: fixed 10 seconds
    MIN_GREEN_DURATION     =  5.0   # Smart mode: never less than 5 s
    MAX_GREEN_DURATION     = 20.0   # Smart mode: never more than 20 s

    def __init__(self, direction: str, green_duration: float = None):
        self.direction      = direction
        self.state          = 'red'
        self.green_duration = green_duration or self.DEFAULT_GREEN_DURATION
        self.time_in_state  = 0.0

    # ── State helpers ────────────────────────────────────────────────────────

    def set_green(self, duration: float = None):
        """Switch to green; optionally override the duration."""
        self.state         = 'green'
        self.time_in_state = 0.0
        if duration is not None:
            self.green_duration = max(self.MIN_GREEN_DURATION,
                                      min(duration, self.MAX_GREEN_DURATION))

    def set_red(self):
        self.state         = 'red'
        self.time_in_state = 0.0

    def is_green(self) -> bool:
        return self.state == 'green'

    # ── Clock tick ───────────────────────────────────────────────────────────

    def tick(self, delta: float) -> bool:
        """
        Advance the internal clock by `delta` seconds.
        Returns True when the green phase has expired.
        """
        self.time_in_state += delta
        if self.state == 'green' and self.time_in_state >= self.green_duration:
            return True
        return False

    # ── Smart duration formula ────────────────────────────────────────────────

    @staticmethod
    def compute_smart_duration(vehicle_count: int, total_vehicles: int) -> float:
        """
        Proportional green-time allocation:
            share    = lane_count / total_count
            duration = MIN + share × (MAX − MIN)

        A lane with zero vehicles gets the minimum 5 s.
        The busiest lane can get up to 20 s.
        """
        if total_vehicles == 0:
            return TrafficLight.MIN_GREEN_DURATION
        share = vehicle_count / total_vehicles
        span  = TrafficLight.MAX_GREEN_DURATION - TrafficLight.MIN_GREEN_DURATION
        return TrafficLight.MIN_GREEN_DURATION + share * span

    def __repr__(self):
        return (f"TrafficLight({self.direction}, {self.state}, "
                f"dur={self.green_duration:.1f}s)")
