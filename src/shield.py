"""Shield charges, invulnerability, and consecutive-break tracking."""

from __future__ import annotations

from src.config import (
    INVULNERABILITY_TICKS,
    OUTSIDE_COLLISION_STEPS_REQUIRED,
    SHIELD_BREAK_GAME_OVER_LIMIT,
)


class ShieldState:
    """Tracks shield charges, post-break invulnerability, and color-fail streaks."""

    def __init__(self) -> None:
        self.charges = 0
        self.invulnerable_ticks = 0
        self.outside_collision_steps = 0
        self.shield_ready = True
        self.consecutive_breaks_without_correct = 0

    def reset(self) -> None:
        self.charges = 0
        self.invulnerable_ticks = 0
        self.outside_collision_steps = 0
        self.shield_ready = True
        self.consecutive_breaks_without_correct = 0

    def is_invulnerable(self) -> bool:
        return self.invulnerable_ticks > 0

    def on_correct_color(self) -> None:
        self.consecutive_breaks_without_correct = 0
        self.charges += 1

    def on_wrong_color_break(self) -> tuple[bool, bool]:
        """Returns (game_over, shield_broke)."""
        broke = False
        if self.charges > 0 and self.shield_ready:
            self.charges -= 1
            self._begin_invulnerability()
            self.consecutive_breaks_without_correct += 1
            broke = True
        game_over = self.consecutive_breaks_without_correct >= SHIELD_BREAK_GAME_OVER_LIMIT
        return game_over, broke

    def try_block_collision(self) -> str | None:
        """Block a fatal collision. Returns 'invuln', 'broke', or None."""
        if self.is_invulnerable():
            return "invuln"
        if self.charges > 0 and self.shield_ready:
            self.charges -= 1
            self._begin_invulnerability()
            return "broke"
        return None

    def try_block_poison(self) -> str | None:
        return self.try_block_collision()

    def on_grid_step(self, head_in_collision_zone: bool) -> None:
        if self.invulnerable_ticks > 0:
            self.invulnerable_ticks -= 1

        if head_in_collision_zone:
            self.outside_collision_steps = 0
        else:
            self.outside_collision_steps += 1
            if self.outside_collision_steps >= OUTSIDE_COLLISION_STEPS_REQUIRED:
                self.shield_ready = True

    def _begin_invulnerability(self) -> None:
        self.invulnerable_ticks = INVULNERABILITY_TICKS
        self.shield_ready = False
        self.outside_collision_steps = 0
