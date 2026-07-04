"""Live-tunable runtime settings (defaults from config.py)."""

from __future__ import annotations

from src import config


class LiveSettings:
    """Mutable gameplay values adjusted via the F1 debug overlay."""

    def __init__(self) -> None:
        self.move_interval_ms = config.MOVE_INTERVAL_MS
        self.desert_slow_multiplier = config.DESERT_SLOW_MULTIPLIER
        self.ice_press_steps = config.ICE_PRESS_STEPS
        self.storm_grace_steps = config.STORM_GRACE_STEPS
        self.portal_cooldown_steps = config.PORTAL_COOLDOWN_STEPS
        self.theme_shift_points = config.THEME_SHIFT_POINTS

    def clamp(self) -> None:
        self.move_interval_ms = max(50, min(400, self.move_interval_ms))
        self.desert_slow_multiplier = max(1, min(5, self.desert_slow_multiplier))
        self.ice_press_steps = max(1, min(10, self.ice_press_steps))
        self.storm_grace_steps = max(0, min(30, self.storm_grace_steps))
        self.portal_cooldown_steps = max(0, min(60, self.portal_cooldown_steps))
        self.theme_shift_points = max(10, min(100, self.theme_shift_points))
