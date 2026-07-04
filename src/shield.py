"""shield charges, invulnerability, and consecutive-break tracking."""

from __future__ import annotations

from src.config import (
    INVULNERABILITY_TICKS,
    OUTSIDE_COLLISION_STEPS_REQUIRED,
    SHIELD_BREAK_GAME_OVER_LIMIT,
)


class ShieldState:
    """shield: 1 wall pass per charge. Wrong color breaks too. 3 consecutive wrong == death."""

    def __init__(self) -> None:
        self.charges = 0
        self.consecutive_breaks_without_correct = 0

    def reset(self) -> None:
        self.charges = 0
        self.consecutive_breaks_without_correct = 0

    def is_invulnerable(self) -> bool:
        return False

    def on_correct_color(self) -> None:
        self.consecutive_breaks_without_correct = 0
        self.charges += 1

    def on_wrong_color_break(self) -> tuple[bool, bool]:
        broke = False
        self.consecutive_breaks_without_correct += 1
        if self.charges > 0:
            self.charges -= 1
            broke = True
        game_over = self.consecutive_breaks_without_correct >= SHIELD_BREAK_GAME_OVER_LIMIT
        return game_over, broke

    def try_block_collision(self) -> str | None:
        if self.charges > 0:
            self.charges -= 1
            return "broke"
        return None

    def try_block_poison(self) -> str | None:
        return self.try_block_collision()

    def on_grid_step(self, head_in_collision_zone: bool) -> None:
        pass
