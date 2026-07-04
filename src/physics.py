"""world movement modifiers: desert, glacier, cyclone/clouds."""

from __future__ import annotations

from typing import Set, Tuple

from src.constants import GRID_HEIGHT, GRID_WIDTH
from src.snake import Direction, Snake
from src.world import DESERT, ICE, STORM, World
from src.config import MOVE_INTERVAL_MS, DESERT_SLOW_MULTIPLIER

Position = Tuple[int, int]

ARROW_KEYS = {"up", "down", "left", "right"}


class PhysicsEngine:

    def __init__(self, world: World, difficulty) -> None:
        self.world = world
        self.difficulty = difficulty
        self.held_arrows: set[str] = set()

        self.storm_mode: str | None = None
        self.storm_frozen_step = 0
        self.storm_poison_count = 0
        self.ate_poison_flag = False
        self.exit_portal_count = 0

    def reset(self) -> None:
        self.held_arrows.clear()
        self.clear_storm_state()
        self.exit_portal_count = 0

    def clear_storm_state(self) -> None:
        self.storm_mode = None
        self.storm_frozen_step = 0
        self.storm_poison_count = 0
        self.ate_poison_flag = False

    def enter_storm_frozen(self) -> None:
        """called when eat poison"""
        self.storm_mode = "frozen"
        self.storm_frozen_step = 0
        self.storm_poison_count += 1
        self.ate_poison_flag = True

    def enter_storm_speed(self, score: int) -> bool:
        """called on exit portal. returns True if 3× speed activates."""
        self.exit_portal_count += 1
        if score >= 100 or self.exit_portal_count >= 2:
            self.storm_mode = "speed"
            return True
        return False

    def on_entry_portal(self) -> None:
        """called when entry portal is used — clears all storm state."""
        self.clear_storm_state()
        self.exit_portal_count = 0

    def on_food_eaten(self) -> None:
        """called when any non-poison food is eaten — exits frozen mode."""
        if self.storm_mode == "frozen":
            self.storm_mode = None
            self.storm_poison_count = 0
            self.ate_poison_flag = False

    def is_speed_boost_active(self, now_ms: int) -> bool:
        return self.storm_mode == "speed"

    def on_key_down(self, key_name: str, score: int) -> None:
        if key_name not in ARROW_KEYS:
            return
        self.held_arrows.add(key_name)
        if self.storm_mode == "frozen":
            self.storm_frozen_step = 1

    def on_key_up(self, key_name: str) -> None:
        if key_name not in ARROW_KEYS:
            return
        self.held_arrows.discard(key_name)

    def move_interval_ms(self, now_ms: int) -> int:
        interval = MOVE_INTERVAL_MS
        if self.world.active_theme == DESERT:
            interval = interval * DESERT_SLOW_MULTIPLIER
        elif self.world.active_theme == ICE and self.held_arrows:
            interval = interval // 2
        if self.storm_mode == "speed":
            interval = max(30, interval // 3)
        return interval

    def allows_movement(self, score: int) -> bool:
        if self.world.active_theme == ICE:
            return len(self.held_arrows) > 0
        if self.storm_mode == "frozen":
            return self.storm_frozen_step > 0
        return True

    def resolve_direction(
        self,
        snake: Snake,
        maze_walls: Set[Position],
        now_ms: int,
        score: int,
    ) -> Direction:
        return snake.direction

    def consume_ice_step(self, score: int) -> None:
        if self.storm_mode == "frozen" and self.storm_frozen_step > 0:
            self.storm_frozen_step -= 1

    def storm_gusts_left(self) -> int:
        return 0

    def on_storm_entered(self) -> None:
        pass

    def activate_speed_boost(self, now_ms: int) -> None:
        pass

def is_safe_head_position(
    position: Position,
    snake: Snake,
    maze_walls: Set[Position],
) -> bool:
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
    from src.scoring import DEATH_MAZE, DEATH_SELF, DEATH_WALL
    head = snake.head
    if head[0] < 0 or head[0] >= GRID_WIDTH or head[1] < 0 or head[1] >= GRID_HEIGHT:
        return DEATH_WALL
    if head in maze_walls:
        return DEATH_MAZE
    if head in snake.body[1:]:
        return DEATH_SELF
    return None
