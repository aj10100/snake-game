"""Console-only sound effect placeholders with mute toggle."""

from __future__ import annotations

SFX_EAT = "Eat"
SFX_TELEPORT = "Teleport"
SFX_SHIELD_GAIN = "ShieldGain"
SFX_SHIELD_LOSS = "ShieldLoss"
SFX_POISON = "Poison"
SFX_RECORD = "Record"
SFX_DIE = "Die"


class SoundManager:
    def __init__(self) -> None:
        self.muted = False

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        state = "muted" if self.muted else "unmuted"
        print(f"[SOUND] Volume {state}")
        return self.muted

    def play(self, effect: str) -> None:
        if self.muted:
            return
        print(f"[SOUND EFFECT] Triggered: {effect}")
