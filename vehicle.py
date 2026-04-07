"""
vehicle.py  —  Vehicle data model
----------------------------------
Represents a single vehicle in the simulation queue.
"""

import time
import random

_vehicle_counter = 0

def _next_id():
    global _vehicle_counter
    _vehicle_counter += 1
    return _vehicle_counter


class Vehicle:
    """
    A vehicle waiting at (or passing through) the intersection.

    Types (with spawn probability):
        car       — 70%  (most common)
        truck     — 20%  (slower to clear)
        ambulance — 10%  (triggers emergency override)
    """

    VEHICLE_TYPES = ['car'] * 7 + ['truck'] * 2 + ['ambulance'] * 1

    def __init__(self, vehicle_type=None):
        self.vehicle_id   = _next_id()
        self.vehicle_type = vehicle_type or random.choice(self.VEHICLE_TYPES)
        self.is_emergency = (self.vehicle_type == 'ambulance')
        self.arrival_time = time.time()
        self.departure_time = None
        self.wait_time      = None

    def depart(self):
        """Record when this vehicle left the queue."""
        self.departure_time = time.time()
        self.wait_time = self.departure_time - self.arrival_time

    def __repr__(self):
        return f"Vehicle(id={self.vehicle_id}, type={self.vehicle_type})"
