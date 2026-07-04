"""Stroop-effect color definitions and progressive ball counts."""

from __future__ import annotations

STROOP_COLORS: dict[str, dict[str, object]] = {
    "violet": {"label": "VIOLET", "rgb": (148, 0, 211)},
    "green": {"label": "GREEN", "rgb": (50, 200, 80)},
    "red": {"label": "RED", "rgb": (220, 60, 60)},
    "yellow": {"label": "YELLOW", "rgb": (230, 210, 50)},
    "pink": {"label": "PINK", "rgb": (255, 105, 180)},
}

STROOP_COLOR_KEYS = list(STROOP_COLORS.keys())


def stroop_label(color_key: str) -> str:
    return str(STROOP_COLORS[color_key]["label"])


def stroop_rgb(color_key: str) -> tuple[int, int, int]:
    rgb = STROOP_COLORS[color_key]["rgb"]
    return (int(rgb[0]), int(rgb[1]), int(rgb[2]))


def ball_count_for_score(score: int) -> int:
    """gradually increase Stroop balls from 2 up to 4."""
    if score < 65:
        return 2
    if score < 85:
        return 3
    return 4
