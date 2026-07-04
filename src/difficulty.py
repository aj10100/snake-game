"""score based difficulty tiers """

from __future__ import annotations

GATE_COLOR_MATCH = 51
GATE_ICE_STORM = 101
GATE_POISON = 151

TIER_NORMAL = 0
TIER_COLOR = 1
TIER_HAZARD = 2
TIER_POISON = 3

TIER_LABELS = {
    TIER_NORMAL: "Normal (0-50)",
    TIER_COLOR: "Color match (51-100)",
    TIER_HAZARD: "Ice/Storm on (101-150)",
    TIER_POISON: "Poison (151+)",
}


class DifficultyManager:
    """progressive feature gates driven by score"""

    def __init__(self) -> None:
        self.force_tier: int | None = None

    def tier_from_score(self, score: int) -> int:
        if score >= GATE_POISON:
            return TIER_POISON
        if score >= GATE_ICE_STORM:
            return TIER_HAZARD
        if score >= GATE_COLOR_MATCH:
            return TIER_COLOR
        return TIER_NORMAL

    def effective_tier(self, score: int) -> int:
        if self.force_tier is not None:
            return self.force_tier
        return self.tier_from_score(score)

    def color_match_active(self, score: int) -> bool:
        return self.effective_tier(score) >= TIER_COLOR

    def ice_storm_active(self, score: int) -> bool:
        return self.effective_tier(score) >= TIER_HAZARD

    def poison_active(self, score: int) -> bool:
        return self.effective_tier(score) >= TIER_POISON

    def tier_label(self, score: int) -> str:
        return TIER_LABELS.get(self.effective_tier(score), "Unknown")

    def cycle_force_tier(self) -> None:
        if self.force_tier is None:
            self.force_tier = TIER_NORMAL
        elif self.force_tier < TIER_POISON:
            self.force_tier += 1
        else:
            self.force_tier = None

    def force_tier_label(self) -> str:
        if self.force_tier is None:
            return "OFF (use score)"
        return TIER_LABELS.get(self.force_tier, "Unknown")
