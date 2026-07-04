"""Score tracking, session identity, and per-run statistics."""

from __future__ import annotations

import uuid

from src.config import POINTS_PER_FOOD

DEATH_WALL = "wall"
DEATH_MAZE = "maze"
DEATH_SELF = "self"
DEATH_POISON = "poison"
DEATH_COLOR_FAIL = "color_fail"

DEATH_LABELS = {
    DEATH_WALL: "Wall collision",
    DEATH_MAZE: "Maze block collision",
    DEATH_SELF: "Self collision",
    DEATH_POISON: "Poison",
    DEATH_COLOR_FAIL: "Three wrong colors in a row",
}


class Session:
    """for the entire time the program is open."""

    def __init__(self) -> None:
        self.session_id = uuid.uuid4().hex[:8].upper()
        self.session_high_score = 0

    def note_score(self, score: int) -> bool:
        """track best score this session. returns True if new session best."""
        if score > self.session_high_score:
            self.session_high_score = score
            return True
        return False


class RunStats:
    """tracks one individual game run within a session."""

    def __init__(self) -> None:
        self.score = 0
        self.death_cause: str | None = None
        self.run_start_ms = 0
        self.run_end_ms = 0

    def start_run(self, now_ms: int) -> None:
        self.score = 0
        self.death_cause = None
        self.run_start_ms = now_ms
        self.run_end_ms = 0

    def record_death(self, cause: str, now_ms: int) -> None:
        self.death_cause = cause
        self.run_end_ms = now_ms

    def add_score(self, points: int) -> None:
        self.score = max(0, self.score + points)

    def add_food_score(self) -> None:
        self.add_score(POINTS_PER_FOOD)

    def survival_seconds(self, now_ms: int) -> float:
        end_ms = self.run_end_ms if self.run_end_ms else now_ms
        elapsed = max(0, end_ms - self.run_start_ms)
        return elapsed / 1000.0

    def death_label(self) -> str:
        if self.death_cause is None:
            return "—"
        return DEATH_LABELS.get(self.death_cause, self.death_cause)
