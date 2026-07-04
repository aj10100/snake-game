"""Food spawning, Stroop balls, poison, and black storm balls."""

from __future__ import annotations

import random
from typing import Iterable, List, Optional, Set, Tuple

from src.config import (
    POISON_SPAWN_CHANCE,
    POINTS_COLOR_WRONG,
    POINTS_PER_FOOD,
    STORM_BALL_HIDDEN_MAX_MS,
    STORM_BALL_HIDDEN_MIN_MS,
    STORM_BALL_VISIBLE_MAX_MS,
    STORM_BALL_VISIBLE_MIN_MS,
)
from src.constants import GRID_HEIGHT, GRID_WIDTH
from src.difficulty import DifficultyManager
from src.snake import Snake
from src.stroop_colors import (
    STROOP_COLOR_KEYS,
    ball_count_for_score,
    stroop_label,
    stroop_rgb,
)

Position = Tuple[int, int]

FOOD_NORMAL = "normal"
FOOD_POISON = "poison"
FOOD_STORM_BALL = "storm_ball"


def _manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Food:
    def __init__(self) -> None:
        self.mode = FOOD_NORMAL
        self.position: Optional[Position] = None
        self.color_items: dict[str, Position] = {}
        self.target_color_key: str = "red"
        self.stroop_ink_key: str = "blue"
        self.poison_position: Optional[Position] = None
        self.storm_ball_position: Optional[Position] = None
        self.storm_ball_phase_end_ms = 0
        self.storm_ball_visible = False

    def clear(self) -> None:
        self.mode = FOOD_NORMAL
        self.position = None
        self.color_items = {}
        self.poison_position = None
        self.storm_ball_position = None
        self.storm_ball_visible = False

    @property
    def target_color_name(self) -> str:
        return stroop_label(self.target_color_key)

    @property
    def stroop_ink_rgb(self) -> tuple[int, int, int]:
        return stroop_rgb(self.stroop_ink_key)

    def update_storm_ball(self, now_ms: int, blocked: Iterable[Position], snake: Snake) -> None:
        """Cycle black storm ball visible / hidden on random timers."""
        if self.storm_ball_visible:
            if now_ms >= self.storm_ball_phase_end_ms:
                self.storm_ball_position = None
                self.storm_ball_visible = False
                self.storm_ball_phase_end_ms = now_ms + random.randint(
                    STORM_BALL_HIDDEN_MIN_MS, STORM_BALL_HIDDEN_MAX_MS
                )
            return

        if now_ms < self.storm_ball_phase_end_ms:
            return

        blocked_set = set(blocked) | set(snake.body) | set(self.all_positions())
        open_cells = self._open_cells(blocked_set)
        if open_cells:
            self.storm_ball_position = random.choice(open_cells)
            self.storm_ball_visible = True
            self.storm_ball_phase_end_ms = now_ms + random.randint(
                STORM_BALL_VISIBLE_MIN_MS, STORM_BALL_VISIBLE_MAX_MS
            )
        else:
            self.storm_ball_phase_end_ms = now_ms + 2000

    def spawn(self, blocked: Iterable[Position], difficulty: DifficultyManager, score: int, snake: Snake) -> None:
        blocked_set = set(blocked)

        if difficulty.color_match_active(score):
            self._spawn_stroop(blocked_set, snake, score)
        else:
            self.color_items = {}
            self._spawn_normal(blocked_set)

        self.poison_position = None
        if difficulty.poison_active(score) and random.random() < POISON_SPAWN_CHANCE:
            poison_blocked = blocked_set | set(self.all_positions()) | set(snake.body)
            self._spawn_poison(poison_blocked)

    def all_positions(self) -> List[Position]:
        positions: List[Position] = []
        if self.position is not None:
            positions.append(self.position)
        positions.extend(self.color_items.values())
        if self.poison_position is not None:
            positions.append(self.poison_position)
        if self.storm_ball_position is not None:
            positions.append(self.storm_ball_position)
        return positions

    def _open_cells(self, blocked: Set[Position]) -> List[Position]:
        return [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in blocked
        ]

    def _spawn_normal(self, blocked: Set[Position]) -> None:
        self.mode = FOOD_NORMAL
        open_cells = self._open_cells(blocked)
        self.position = random.choice(open_cells) if open_cells else None

    def _spawn_poison(self, blocked: Set[Position]) -> None:
        open_cells = self._open_cells(blocked)
        self.poison_position = random.choice(open_cells) if open_cells else None

    def _pick_stroop_ink(self, target_key: str) -> str:
        others = [key for key in STROOP_COLOR_KEYS if key != target_key]
        return random.choice(others)

    def _spawn_stroop(self, blocked: Set[Position], snake: Snake, score: int) -> None:
        self.mode = "color"
        self.position = None
        ball_count = ball_count_for_score(score)

        self.target_color_key = random.choice(STROOP_COLOR_KEYS)
        self.stroop_ink_key = self._pick_stroop_ink(self.target_color_key)

        head = snake.head
        body_set = set(snake.body)
        safe_cells = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in blocked
            and (x, y) not in body_set
            and _manhattan((x, y), head) >= 3
        ]
        if len(safe_cells) < ball_count:
            safe_cells = self._open_cells(blocked | body_set)

        if len(safe_cells) < ball_count:
            self.color_items = {}
            self._spawn_normal(blocked)
            return

        pool = STROOP_COLOR_KEYS.copy()
        random.shuffle(pool)
        chosen_colors = pool[:ball_count]
        if self.target_color_key not in chosen_colors:
            chosen_colors[-1] = self.target_color_key

        random.shuffle(safe_cells)
        self.color_items = {
            color_key: safe_cells[index]
            for index, color_key in enumerate(chosen_colors)
        }

    def item_at(self, position: Position) -> Optional[str]:
        if self.mode == FOOD_NORMAL and self.position == position:
            return FOOD_NORMAL
        if self.storm_ball_position == position:
            return FOOD_STORM_BALL
        if self.poison_position == position:
            return FOOD_POISON
        for color_key, pos in self.color_items.items():
            if pos == position:
                return color_key
        return None

    def is_at(self, position: Position) -> bool:
        return self.item_at(position) is not None

    def respawn_color_pair(self, blocked: Iterable[Position], snake: Snake, score: int) -> None:
        self.color_items = {}
        self._spawn_stroop(set(blocked), snake, score)

    def handle_eat(self, position: Position) -> tuple[str, int]:
        kind = self.item_at(position)
        if kind is None:
            return ("none", 0)

        if kind == FOOD_NORMAL:
            self.position = None
            return ("normal", POINTS_PER_FOOD)

        if kind == FOOD_STORM_BALL:
            self.storm_ball_position = None
            self.storm_ball_visible = False
            self.storm_ball_phase_end_ms = 0
            return ("storm_ball", 0)

        if kind == FOOD_POISON:
            self.poison_position = None
            return ("poison", 0)

        self.color_items = {}
        if kind == self.target_color_key:
            return ("color_correct", POINTS_PER_FOOD)
        return ("color_wrong", -POINTS_COLOR_WRONG)
