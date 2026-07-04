"""paired teleporters- spawn rules, visibility cycle, teleportation, and cooldown."""

from __future__ import annotations

import random
from typing import Iterable, Literal, Optional, Set, Tuple

from src.config import (
    PORTAL_CLEARANCE,
    PORTAL_HIDDEN_MAX_MS,
    PORTAL_HIDDEN_MIN_MS,
    PORTAL_VISIBLE_MAX_MS,
    PORTAL_VISIBLE_MIN_MS,
    PORTAL_COOLDOWN_STEPS,
)
from src.constants import GRID_HEIGHT, GRID_WIDTH
from src.physics import is_safe_head_position
from src.snake import Snake
from src.world import World

Position = Tuple[int, int]
PortalKind = Literal["entrance", "exit"]


def _in_bounds(x: int, y: int) -> bool:
    return 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT


def _clearance_cells(center: Position) -> Set[Position]:
    cx, cy = center
    cells: Set[Position] = set()
    for dx in range(-PORTAL_CLEARANCE, PORTAL_CLEARANCE + 1):
        for dy in range(-PORTAL_CLEARANCE, PORTAL_CLEARANCE + 1):
            nx, ny = cx + dx, cy + dy
            if _in_bounds(nx, ny):
                cells.add((nx, ny))
    return cells


def _has_clearance(center: Position, blocked: Set[Position]) -> bool:
    for cell in _clearance_cells(center):
        if cell != center and cell in blocked:
            return False
    return True


class PortalManager:

    def __init__(self) -> None:
        self.entrance: Optional[Position] = None
        self.exit: Optional[Position] = None
        self.cooldown_steps = 0
        self.visible = False
        self.phase_end_ms = 0

    def reset(self, now_ms: int) -> None:
        self.entrance = None
        self.exit = None
        self.cooldown_steps = 0
        self.visible = False
        self.phase_end_ms = now_ms + random.randint(PORTAL_HIDDEN_MIN_MS, PORTAL_HIDDEN_MAX_MS)

    def blocked_cells(self) -> Set[Position]:
        if not self.visible:
            return set()
        blocked: Set[Position] = set()
        if self.entrance is not None:
            blocked.add(self.entrance)
        if self.exit is not None:
            blocked.add(self.exit)
        return blocked

    def spawn(self, blocked: Iterable[Position]) -> bool:
        blocked_set = set(blocked)
        candidates = [
            (x, y)
            for x in range(PORTAL_CLEARANCE, GRID_WIDTH - PORTAL_CLEARANCE)
            for y in range(PORTAL_CLEARANCE, GRID_HEIGHT - PORTAL_CLEARANCE)
            if _has_clearance((x, y), blocked_set)
        ]
        random.shuffle(candidates)

        self.entrance = None
        self.exit = None

        for entrance in candidates:
            entrance_zone = _clearance_cells(entrance)
            remaining = [
                pos
                for pos in candidates
                if pos != entrance and pos not in entrance_zone and _has_clearance(pos, blocked_set | entrance_zone)
            ]
            if not remaining:
                continue
            self.entrance = entrance
            self.exit = random.choice(remaining)
            return True
        return False

    def update(self, now_ms: int, blocked: Iterable[Position]) -> None:
        if now_ms < self.phase_end_ms:
            return
        if self.visible:
            self._begin_hidden_phase(now_ms)
        else:
            self._begin_visible_phase(now_ms, blocked)

    def _begin_hidden_phase(self, now_ms: int) -> None:
        self.entrance = None
        self.exit = None
        self.visible = False
        self.phase_end_ms = now_ms + random.randint(PORTAL_HIDDEN_MIN_MS, PORTAL_HIDDEN_MAX_MS)

    def _begin_visible_phase(self, now_ms: int, blocked: Iterable[Position]) -> None:
        if self.spawn(blocked):
            self.visible = True
            self.phase_end_ms = now_ms + random.randint(PORTAL_VISIBLE_MIN_MS, PORTAL_VISIBLE_MAX_MS)
        else:
            self.phase_end_ms = now_ms + 2000

    def on_grid_step(self) -> None:
        if self.cooldown_steps > 0:
            self.cooldown_steps -= 1

    def try_teleport(
        self,
        snake: Snake,
        world: World,
        maze_walls: Set[Position],
        now_ms: int,
    ) -> tuple[Optional[str], Optional[PortalKind]]:
        """
        entrance - exit + random theme. exit - entrance + storm theme.
        """
        if not self.visible or self.cooldown_steps > 0 or self.entrance is None or self.exit is None:
            return None, None

        used: PortalKind | None = None
        target: Position | None = None

        if snake.head == self.entrance:
            target = self.exit
            used = "entrance"
        elif snake.head == self.exit:
            target = self.entrance
            used = "exit"
        else:
            return None, None

        if not is_safe_head_position(target, snake, maze_walls):
            return None, None

        snake.teleport_head(target)
        self.cooldown_steps = PORTAL_COOLDOWN_STEPS
        self._begin_hidden_phase(now_ms)

        previous_theme = world.active_theme
        if used == "entrance":
            world.portal_shift_theme(now_ms)
        else:
            world.enter_storm(now_ms)
        return previous_theme, used

    def is_on_cooldown(self) -> bool:
        return self.cooldown_steps > 0

    def cooldown_steps_remaining(self) -> int:
        return self.cooldown_steps

    def ms_until_phase_change(self, now_ms: int) -> int:
        return max(0, self.phase_end_ms - now_ms)

    def visibility_label(self) -> str:
        return "visible" if self.visible else "hidden"
