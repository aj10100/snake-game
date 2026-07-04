"""map themes, backgrounds, maze layout, and portal-driven theme changes."""

from __future__ import annotations

import random
from typing import Set, Tuple

from src.constants import GRID_HEIGHT, GRID_WIDTH, THEME_LABELS, THEME_PALETTES

Position = Tuple[int, int]

FOREST = "forest"
DESERT = "desert"
ICE = "ice"
STORM = "storm"
MAZE = "maze"

ALL_THEMES = [FOREST, DESERT, ICE, STORM, MAZE]
PORTAL_THEMES = [FOREST, DESERT, ICE, MAZE]

# WIND_LABELS = {
#     (1, 0): "EAST",
#     (-1, 0): "WEST",
#     (0, -1): "NORTH",
#     (0, 1): "SOUTH",
# }


def build_maze_walls() -> Set[Position]:
    walls: Set[Position] = set()
    for cx in range(6, GRID_WIDTH - 6, 8):
        for cy in range(6, GRID_HEIGHT - 6, 8):
            for dx in range(2):
                for dy in range(2):
                    walls.add((cx + dx, cy + dy))
    return walls


def _has_one_by_one_pocket(walls: Set[Position]) -> bool:
    for x in range(1, GRID_WIDTH - 1):
        for y in range(1, GRID_HEIGHT - 1):
            if (x, y) in walls:
                continue
            neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            if all(n in walls or n[0] < 0 or n[0] >= GRID_WIDTH or n[1] < 0 or n[1] >= GRID_HEIGHT for n in neighbors):
                return True
    return False


MAZE_WALLS = build_maze_walls()
assert not _has_one_by_one_pocket(MAZE_WALLS), "Maze layout must not create 1x1 dead-end pockets"


class World:
    """active theme, palette, maze walls — themes change only via portals or storm triggers."""

    def __init__(self) -> None:
        self.active_theme = FOREST

    def reset(self) -> None:
        self.active_theme = FOREST

    @property
    def label(self) -> str:
        return THEME_LABELS.get(self.active_theme, self.active_theme.title())

    @property
    def storm_wind_label(self) -> str:
        return ""

    @property
    def background_color(self) -> tuple[int, int, int]:
        return THEME_PALETTES[self.active_theme][0]

    @property
    def grid_line_color(self) -> tuple[int, int, int]:
        return THEME_PALETTES[self.active_theme][1]

    @property
    def maze_walls(self) -> Set[Position]:
        if self.active_theme == MAZE:
            return MAZE_WALLS
        return set()

    def blocked_cells(self) -> Set[Position]:
        return set(self.maze_walls)

    def storm_is_approaching(self) -> bool:
        return False

    def is_storm_alert_active(self, now_ms: int) -> bool:
        return False

    def storm_wind_active(self, now_ms: int) -> bool:
        return False

    def on_food_scored(self, points: int, now_ms: int) -> bool:
        return False

    def portal_shift_theme(self, now_ms: int = 0) -> None:
        """entrance portal - random non-storm theme."""
        choices = [t for t in PORTAL_THEMES if t != self.active_theme]
        if not choices:
            choices = PORTAL_THEMES.copy()
        self.set_theme(random.choice(choices), now_ms)

    def enter_storm(self, now_ms: int = 0) -> None:
        """exit portal / storm ball: switch to storm """
        self.set_theme(STORM, now_ms)



    def set_theme(self, theme: str, now_ms: int = 0) -> None:
        self.active_theme = theme


    def on_grid_step(self) -> None:
        pass

    def _begin_storm_entry(self) -> None:
        pass

    def _pick_storm_wind(self) -> None:
        pass

    def points_until_shift(self) -> int:
        return 0
