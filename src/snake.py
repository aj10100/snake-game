"""snake movement, growth, and collision."""

from __future__ import annotations

from typing import List, Tuple

from src.constants import GRID_HEIGHT, GRID_WIDTH

Position = Tuple[int, int]
Direction = Tuple[int, int]

UP: Direction = (0, -1)
DOWN: Direction = (0, 1)
LEFT: Direction = (-1, 0)
RIGHT: Direction = (1, 0)

DIRECTION_BY_KEY = {
    "up": UP,
    "down": DOWN,
    "left": LEFT,
    "right": RIGHT,
}


def is_opposite(a: Direction, b: Direction) -> bool:
    return a[0] == -b[0] and a[1] == -b[1]


class Snake:
    def __init__(self, start: Position | None = None) -> None:
        if start is None:
            start = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
        self.body: List[Position] = [start, (start[0] - 1, start[1]), (start[0] - 2, start[1])]
        self.direction: Direction = RIGHT
        self.grow_pending = 0

    @property
    def head(self) -> Position:
        return self.body[0]

    def set_direction(self, new_direction: Direction) -> None:
        if is_opposite(new_direction, self.direction):
            return
        self.direction = new_direction

    def set_direction_from_key(self, key_name: str) -> None:
        direction = DIRECTION_BY_KEY.get(key_name)
        if direction is not None:
            self.set_direction(direction)

    def queue_growth(self, segments: int = 1) -> None:
        self.grow_pending += segments

    def snapshot(self) -> tuple[list[Position], Direction, int]:
        return (list(self.body), self.direction, self.grow_pending)

    def restore(self, snap: tuple[list[Position], Direction, int]) -> None:
        self.body, self.direction, self.grow_pending = list(snap[0]), snap[1], snap[2]

    def move(self, direction: Direction | None = None) -> None:
        hx, hy = self.head
        dx, dy = direction if direction is not None else self.direction
        new_head = (hx + dx, hy + dy)
        self.body.insert(0, new_head)

        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

    def teleport_head(self, new_head: Position) -> None:
        self.body[0] = new_head

    def occupies(self, position: Position) -> bool:
        return position in self.body
