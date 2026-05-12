"""Timer scheduling primitives for Threepio periodic callbacks."""

from __future__ import annotations

import time
from typing import Callable


class Timer:
    """A timer for syncing things that run at different, variable rates."""

    def __init__(self, period: int, callback: Callable[[], None], name: str = "", log: bool = False):
        self.period = period  # ms
        self.callback = callback
        self.anchor_time: float = time.time()
        self.name = name
        self.log = log

    def run(self) -> None:
        self.callback()

    def run_if_appropriate(self) -> bool:
        if self.period <= 0:
            return False

        current_time = time.time()
        elapsed_periods, extra_time = divmod(current_time - self.anchor_time, self.period / 1000)
        if elapsed_periods > 0:
            self.anchor_time = current_time - extra_time
            self.run()
            return True
        return False

    def set_period(self, new_period: int) -> None:
        if self.period != new_period:
            self.anchor_time = time.time()
        self.period = new_period

    def cancel(self) -> None:
        self.period = 0


class TimerManager:
    """Owns and runs `Timer` objects."""

    def __init__(self):
        self.timers: list[Timer] = []

    def add_timer(self, period: int, callback: Callable[[], None], name: str = "", log: bool = False) -> Timer:
        timer = Timer(period, callback, name, log)
        self.timers.append(timer)
        return timer

    def run_timers(self) -> None:
        for timer in self.timers:
            timer.run_if_appropriate()

    def reset_timer_anchors(self) -> None:
        current_time = time.time()
        for timer in self.timers:
            timer.anchor_time = current_time
