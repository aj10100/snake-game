"""Environmental movement modifiers: desert, ice, and storm."""

from __future__ import annotations

import random
from typing import Set, Tuple

from src.config import SPEED_BOOST_MS, STORM_GUST_MAX, STORM_GUST_MIN
from src.difficulty import DifficultyManager
from src.live_settings import LiveSettings
from src.snake import Direction, Snake
from src.world import DESERT, ICE, STORM, World

Position = Tuple[int, int]

ARROW_KEYS = {"up", "down", "left", "right"}


class PhysicsEngine:
    """Applies theme-specific timing and direction rules to grid movement."""

    def __init__(self, world: World, live: LiveSettings, difficulty: "DifficultyManager") -> None:
        self.world = world
        self.live = live
        self.difficulty = difficulty
        self.held_arrows: set[str] = set()
        self.ice_steps_remaining = 0
        self.storm_gusts_remaining = 0
        self.speed_boost_until_ms = 0

    def reset(self) -> None:
        self.held_arrows.clear()
        self.ice_steps_remaining = 0
        self.storm_gusts_remaining = 0
        self.speed_boost_until_ms = 0

    def activate_speed_boost(self, now_ms: int) -> None:
        self.speed_boost_until_ms = now_ms + SPEED_BOOST_MS

    def is_speed_boost_active(self, now_ms: int) -> bool:
        return now_ms < self.speed_boost_until_ms

    def on_storm_entered(self) -> None:
        """Arm a short burst of 1–2 wind gusts when entering storm."""
        self.storm_gusts_remaining = random.randint(STORM_GUST_MIN, STORM_GUST_MAX)

    def on_key_down(self, key_name: str, score: int) -> None:
        if key_name not in ARROW_KEYS:
            return
        self.held_arrows.add(key_name)
        if (
            self.world.active_theme == ICE
            and self.difficulty.ice_storm_active(score)
        ):
            self.ice_steps_remaining = self.live.ice_press_steps

    def on_key_up(self, key_name: str) -> None:
        if key_name not in ARROW_KEYS:
            return
        self.held_arrows.discard(key_name)

    def move_interval_ms(self, now_ms: int) -> int:
        interval = self.live.move_interval_ms
        if self.world.active_theme == DESERT and not self.held_arrows:
            interval = self.live.move_interval_ms * self.live.desert_slow_multiplier
        if self.is_speed_boost_active(now_ms):
            interval = max(30, interval // 3)
        return interval

    def allows_movement(self, score: int) -> bool:
        if self.world.active_theme == ICE and self.difficulty.ice_storm_active(score):
            return self.ice_steps_remaining > 0
        return True

    def resolve_direction(
        self,
        snake: Snake,
        maze_walls: Set[Position],
        now_ms: int,
        score: int,
    ) -> Direction:
        storm_burst = (
            self.world.active_theme == STORM
            and self.difficulty.ice_storm_active(score)
            and self.world.storm_wind_active(now_ms)
            and self.storm_gusts_remaining > 0
        )
        if storm_burst:
            self.storm_gusts_remaining -= 1
            wind = self.world.storm_wind_direction
            target = (snake.head[0] + wind[0], snake.head[1] + wind[1])
            if is_safe_head_position(target, snake, maze_walls):
                snake.direction = wind
                return wind

        return snake.direction

    def storm_gusts_left(self) -> int:
        return self.storm_gusts_remaining

    def consume_ice_step(self, score: int) -> None:
        if (
            self.world.active_theme == ICE
            and self.difficulty.ice_storm_active(score)
            and self.ice_steps_remaining > 0
        ):
            self.ice_steps_remaining -= 1


def is_safe_head_position(
    position: Position,
    snake: Snake,
    maze_walls: Set[Position],
) -> bool:
    from src.constants import GRID_HEIGHT, GRID_WIDTH

    x, y = position
    if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
        return False
    if position in maze_walls:
        return False
    tail_will_move = snake.grow_pending == 0
    body_to_check = snake.body if not tail_will_move else snake.body[:-1]
    return position not in body_to_check


def head_in_collision_zone(snake: Snake, maze_walls: Set[Position]) -> bool:
    return collides_after_move(snake, maze_walls) is not None


def collides_after_move(
    snake: Snake,
    maze_walls: Set[Position],
) -> str | None:
    """Return death cause if the snake head is in an illegal cell."""
    from src.scoring import DEATH_MAZE, DEATH_SELF, DEATH_WALL

    head = snake.head
    from src.constants import GRID_HEIGHT, GRID_WIDTH

    if head[0] < 0 or head[0] >= GRID_WIDTH or head[1] < 0 or head[1] >= GRID_HEIGHT:
        return DEATH_WALL
    if head in maze_walls:
        return DEATH_MAZE
    if head in snake.body[1:]:
        return DEATH_SELF
    return None
