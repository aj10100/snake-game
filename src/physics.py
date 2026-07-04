"""Environmental movement modifiers: desert, ice/glacier, storm/clouds."""

from __future__ import annotations

from typing import Set, Tuple

from src.constants import GRID_HEIGHT, GRID_WIDTH
from src.snake import Direction, Snake
from src.world import DESERT, ICE, STORM, World
from src.config import MOVE_INTERVAL_MS, DESERT_SLOW_MULTIPLIER

Position = Tuple[int, int]

ARROW_KEYS = {"up", "down", "left", "right"}


class PhysicsEngine:
    """Theme-specific timing and direction rules for grid movement."""

    def __init__(self, world: World, difficulty) -> None:
        self.world = world
        self.difficulty = difficulty
        self.held_arrows: set[str] = set()

        # Storm state
        self.storm_mode: str | None = None  # "frozen" | "speed" | None
        self.storm_frozen_step = 0          # 0 or 1, granted by key press
        self.storm_poison_count = 0         # consecutive poisons in storm
        self.ate_poison_flag = False         # set on poison eat, cleared on food/theme
        self.exit_portal_count = 0          # consecutive exit portal uses

    def reset(self) -> None:
        self.held_arrows.clear()
        self.clear_storm_state()
        self.exit_portal_count = 0

    # ── Storm helpers ──────────────────────────────────────────────

    def clear_storm_state(self) -> None:
        self.storm_mode = None
        self.storm_frozen_step = 0
        self.storm_poison_count = 0
        self.ate_poison_flag = False

    def enter_storm_frozen(self) -> None:
        """Called when eating poison (storm ball)."""
        self.storm_mode = "frozen"
        self.storm_frozen_step = 0
        self.storm_poison_count += 1
        self.ate_poison_flag = True

    def enter_storm_speed(self, score: int) -> bool:
        """Called on exit portal. Returns True if 3× speed activates."""
        self.exit_portal_count += 1
        if score >= 100 or self.exit_portal_count >= 2:
            self.storm_mode = "speed"
            return True
        return False

    def on_entry_portal(self) -> None:
        """Called when entry portal is used — clears all storm state."""
        self.clear_storm_state()
        self.exit_portal_count = 0

    def on_food_eaten(self) -> None:
        """Called when any non-poison food is eaten — exits frozen mode."""
        if self.storm_mode == "frozen":
            self.storm_mode = None
            self.storm_poison_count = 0
            self.ate_poison_flag = False

    def is_speed_boost_active(self, now_ms: int) -> bool:
        return self.storm_mode == "speed"

    # ── Key handling ───────────────────────────────────────────────

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

    # ── Movement rules ─────────────────────────────────────────────

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
        # No more storm wind — always use snake's own direction
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



# """Environmental movement modifiers: desert, ice, and storm."""

# from __future__ import annotations

# import random
# from typing import Set, Tuple

# from src.config import SPEED_BOOST_MS, STORM_GUST_MAX, STORM_GUST_MIN
# from src.difficulty import DifficultyManager
# from src.live_settings import LiveSettings
# from src.snake import Direction, Snake
# from src.world import DESERT, ICE, STORM, World

# Position = Tuple[int, int]

# ARROW_KEYS = {"up", "down", "left", "right"}


# class PhysicsEngine:
#     """Applies theme-specific timing and direction rules to grid movement."""

#     def __init__(self, world: World, live: LiveSettings, difficulty: "DifficultyManager") -> None:
#         self.world = world
#         self.live = live
#         self.difficulty = difficulty
#         self.held_arrows: set[str] = set()
#         self.ice_steps_remaining = 0
#         self.storm_gusts_remaining = 0
#         self.speed_boost_until_ms = 0

#     def reset(self) -> None:
#         self.held_arrows.clear()
#         self.ice_steps_remaining = 0
#         self.storm_gusts_remaining = 0
#         self.speed_boost_until_ms = 0

#     def activate_speed_boost(self, now_ms: int) -> None:
#         self.speed_boost_until_ms = now_ms + SPEED_BOOST_MS

#     def is_speed_boost_active(self, now_ms: int) -> bool:
#         return now_ms < self.speed_boost_until_ms

#     def on_storm_entered(self) -> None:
#         """Arm a short burst of 1–2 wind gusts when entering storm."""
#         self.storm_gusts_remaining = random.randint(STORM_GUST_MIN, STORM_GUST_MAX)

#     def on_key_down(self, key_name: str, score: int) -> None:
#         if key_name not in ARROW_KEYS:
#             return
#         self.held_arrows.add(key_name)
#         if self.world.active_theme == ICE :
#             self.ice_steps_remaining = self.live.ice_press_steps

#     def on_key_up(self, key_name: str) -> None:
#         if key_name not in ARROW_KEYS:
#             return
#         self.held_arrows.discard(key_name)

#     def move_interval_ms(self, now_ms: int) -> int:
#         interval = self.live.move_interval_ms
#         if self.world.active_theme == DESERT and not self.held_arrows:
#             interval = self.live.move_interval_ms * self.live.desert_slow_multiplier
#         if self.is_speed_boost_active(now_ms):
#             interval = max(30, interval // 3)
#         return interval

#     def allows_movement(self, score: int) -> bool:
#         if self.world.active_theme == ICE :
#             return self.ice_steps_remaining > 0
#         return True

#     def resolve_direction(
#         self,
#         snake: Snake,
#         maze_walls: Set[Position],
#         now_ms: int,
#         score: int,
#     ) -> Direction:
#         storm_burst = (
#             self.world.active_theme == STORM
#             and self.difficulty.ice_storm_active(score)
#             and self.world.storm_wind_active(now_ms)
#             and self.storm_gusts_remaining > 0
#         )
#         if storm_burst:
#             self.storm_gusts_remaining -= 1
#             wind = self.world.storm_wind_direction
#             target = (snake.head[0] + wind[0], snake.head[1] + wind[1])
#             if is_safe_head_position(target, snake, maze_walls):
#                 snake.direction = wind
#                 return wind

#         return snake.direction

#     def storm_gusts_left(self) -> int:
#         return self.storm_gusts_remaining

#     def consume_ice_step(self, score: int) -> None:
#         if  self.world.active_theme == ICE  and self.ice_steps_remaining > 0 :
#             self.ice_steps_remaining -= 1


# def is_safe_head_position(
#     position: Position,
#     snake: Snake,
#     maze_walls: Set[Position],
# ) -> bool:
#     from src.constants import GRID_HEIGHT, GRID_WIDTH

#     x, y = position
#     if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
#         return False
#     if position in maze_walls:
#         return False
#     tail_will_move = snake.grow_pending == 0
#     body_to_check = snake.body if not tail_will_move else snake.body[:-1]
#     return position not in body_to_check


# def head_in_collision_zone(snake: Snake, maze_walls: Set[Position]) -> bool:
#     return collides_after_move(snake, maze_walls) is not None


# def collides_after_move(
#     snake: Snake,
#     maze_walls: Set[Position],
# ) -> str | None:
#     """Return death cause if the snake head is in an illegal cell."""
#     from src.scoring import DEATH_MAZE, DEATH_SELF, DEATH_WALL

#     head = snake.head
#     from src.constants import GRID_HEIGHT, GRID_WIDTH

#     if head[0] < 0 or head[0] >= GRID_WIDTH or head[1] < 0 or head[1] >= GRID_HEIGHT:
#         return DEATH_WALL
#     if head in maze_walls:
#         return DEATH_MAZE
#     if head in snake.body[1:]:
#         return DEATH_SELF
#     return None
