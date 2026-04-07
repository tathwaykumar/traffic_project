"""
simulation.py  —  Core simulation engine
-----------------------------------------
Manages four lane queues, four traffic lights, vehicle spawning,
signal rotation, emergency override, and statistics collection.
"""

import time
import random
from collections import deque

from vehicle import Vehicle
from traffic_light import TrafficLight
from utils import should_spawn_vehicle, compute_average_wait, compute_throughput

DIRECTIONS = ['North', 'South', 'East', 'West']
DEFAULT_ARRIVAL_RATE = 0.4   # vehicles per second per lane


class Simulation:
    """
    Full 4-way intersection simulation.

    Modes
    -----
    'normal' : every lane gets DEFAULT_GREEN_DURATION (10 s) in round-robin.
    'smart'  : green duration is proportional to the lane's current queue size.

    Emergency override
    ------------------
    When an ambulance arrives, its lane immediately receives the green light,
    preempting the normal rotation. Once the ambulance clears, rotation resumes.
    """

    def __init__(self, mode: str = 'normal',
                 arrival_rate: float = DEFAULT_ARRIVAL_RATE):
        self.mode         = mode
        self.arrival_rate = arrival_rate
        self.start_time   = time.time()
        self.last_tick    = time.time()
        self.running      = False
        self.paused       = False

        # Lane queues
        self.lanes = {d: deque() for d in DIRECTIONS}

        # Traffic lights (all start red)
        self.lights = {d: TrafficLight(d) for d in DIRECTIONS}

        # Give the first lane a green to start
        self.current_green = DIRECTIONS[0]
        self.lights[self.current_green].set_green()

        # Statistics
        self.departed     = []   # vehicles that cleared the intersection
        self.total_spawned = 0

        # Emergency
        self.emergency_dir = None

        # GUI callback: set from outside to receive state snapshots
        self.on_tick_callback = None

    # ── Control ──────────────────────────────────────────────────────────────

    def start(self):
        self.running = True
        self.paused  = False

    def pause(self):
        self.paused = not self.paused

    def stop(self):
        self.running = False

    def reset(self):
        self.__init__(mode=self.mode, arrival_rate=self.arrival_rate)

    # ── Manual vehicle injection ──────────────────────────────────────────────

    def spawn_vehicle(self, direction: str, vehicle_type: str = None):
        v = Vehicle(vehicle_type=vehicle_type)
        self.lanes[direction].append(v)
        self.total_spawned += 1
        if v.is_emergency:
            self.emergency_dir = direction

    def spawn_emergency(self, direction: str):
        self.spawn_vehicle(direction, vehicle_type='ambulance')

    # ── Main tick (call every ~100 ms) ────────────────────────────────────────

    def tick(self):
        if not self.running or self.paused:
            return

        now   = time.time()
        delta = now - self.last_tick
        self.last_tick = now

        self._spawn_vehicles(delta)
        self._handle_emergency()
        self._move_vehicles(delta)
        self._advance_signal(delta)

        if self.on_tick_callback:
            self.on_tick_callback(self._snapshot())

    # ── Private helpers ───────────────────────────────────────────────────────

    def _spawn_vehicles(self, delta):
        for d in DIRECTIONS:
            if should_spawn_vehicle(self.arrival_rate, delta):
                v = Vehicle()
                self.lanes[d].append(v)
                self.total_spawned += 1
                if v.is_emergency:
                    self.emergency_dir = d

    def _handle_emergency(self):
        if self.emergency_dir is None:
            return
        lane = self.lanes[self.emergency_dir]
        if not any(v.is_emergency for v in lane):
            self.emergency_dir = None
            return
        if self.current_green != self.emergency_dir:
            self._switch_green_to(self.emergency_dir)

    def _move_vehicles(self, delta):
        lane = self.lanes[self.current_green]
        if not lane:
            return
        # ~2 vehicles per second; probabilistic so flow is smooth
        if random.random() < 2.0 * delta:
            v = lane.popleft()
            v.depart()
            self.departed.append(v)
            if v.is_emergency:
                self.emergency_dir = None

    def _advance_signal(self, delta):
        expired = self.lights[self.current_green].tick(delta)
        if expired:
            idx      = DIRECTIONS.index(self.current_green)
            next_dir = DIRECTIONS[(idx + 1) % len(DIRECTIONS)]
            self._switch_green_to(next_dir)

    def _switch_green_to(self, direction: str):
        self.lights[self.current_green].set_red()
        if self.mode == 'smart':
            total    = sum(len(q) for q in self.lanes.values())
            count    = len(self.lanes[direction])
            duration = TrafficLight.compute_smart_duration(count, total)
        else:
            duration = TrafficLight.DEFAULT_GREEN_DURATION
        self.lights[direction].set_green(duration)
        self.current_green = direction

    # ── Snapshot for GUI ──────────────────────────────────────────────────────

    def _snapshot(self) -> dict:
        elapsed = time.time() - self.start_time
        return {
            'mode':          self.mode,
            'elapsed':       elapsed,
            'current_green': self.current_green,
            'emergency_dir': self.emergency_dir,
            'lane_counts':   {d: len(self.lanes[d]) for d in DIRECTIONS},
            'light_states':  {d: self.lights[d].state for d in DIRECTIONS},
            'light_time_left': {
                d: max(0.0, self.lights[d].green_duration
                            - self.lights[d].time_in_state)
                for d in DIRECTIONS
            },
            'green_duration': {
                d: self.lights[d].green_duration for d in DIRECTIONS
            },
            'total_spawned': self.total_spawned,
            'total_cleared': len(self.departed),
            'avg_wait':      compute_average_wait(self.departed),
            'throughput':    compute_throughput(self.departed, elapsed),
            'front_vehicle': {
                d: self.lanes[d][0].vehicle_type if self.lanes[d] else None
                for d in DIRECTIONS
            },
        }

    def get_stats(self) -> dict:
        elapsed = time.time() - self.start_time
        return {
            'mode':          self.mode,
            'total_spawned': self.total_spawned,
            'total_cleared': len(self.departed),
            'avg_wait':      compute_average_wait(self.departed),
            'throughput':    compute_throughput(self.departed, elapsed),
            'elapsed':       elapsed,
        }
