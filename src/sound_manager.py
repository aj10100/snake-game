"""Real pygame.mixer sound effects and background music."""

from __future__ import annotations
import os
import pygame

ASSETS = "assets"

SFX_EAT          = "eat"
SFX_TELEPORT     = "teleport_enter"
SFX_TELEPORT_OUT = "teleport_exit"
SFX_SHIELD_GAIN  = "shield"
SFX_SHIELD_LOSS  = "dead_ding"
SFX_POISON       = "poison"
SFX_RECORD       = "high_score"
SFX_DIE          = "dead_ding"
SFX_MOVE_CLOUD   = "move_cloud"
SFX_MOVE_GLACIER = "move_glacier"
SFX_OPTION_CHOOSE = "option_choose"

# music tracks keyed by world theme name
THEME_MUSIC = {
    "forest":  "forest_desert_background.mp3",
    "desert":  "forest_desert_background.mp3",
    "ice":     "glacier_maze_background.mp3",
    "storm":   "storm_background.mp3",
    "maze":    "glacier_maze_background.mp3",
}

class SoundManager:
    def __init__(self) -> None:
        pygame.mixer.init()
        self.muted = False
        self._current_music_theme: str | None = None

        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        self._load_sounds()

    def _load_sounds(self) -> None:
        mapping = {
            SFX_EAT:          "eat_wrongFood_poison.mp3",
            SFX_POISON:       "eat_wrongFood_poison.mp3",
            SFX_TELEPORT:     "entry_portal_enter.mp3",
            SFX_TELEPORT_OUT: "exit_portal_enter.mp3",
            SFX_DIE:          "dead_ding.wav",
            SFX_SHIELD_LOSS:  "dead_ding.wav",
            SFX_RECORD:       "high_score_popup.mp3",
            SFX_MOVE_CLOUD:   "snake_move_cloud_cyclone.mp3",
            SFX_MOVE_GLACIER: "glacier_move.mp3",
            SFX_OPTION_CHOOSE: "option_choose.mp3",
        }
        for key, filename in mapping.items():
            path = os.path.join(ASSETS, filename)
            try:
                self._sounds[key] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"[SOUND] Could not load {path}: {e}")
                self._sounds[key] = None

    def play(self, effect: str) -> None:
        if self.muted:
            return
        snd = self._sounds.get(effect)
        if snd:
            snd.play()

    def play_theme_music(self, theme: str) -> None:
        """wwitch background music when the world theme changes."""
        if self.muted:
            return

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        filename = THEME_MUSIC.get(theme)
        if not filename:
            return
        # only switch if the music file is different
        if self._current_music_theme == filename:
            return
        path = os.path.join(ASSETS, filename)
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)   # loop forever
            self._current_music_theme = filename
        except Exception as e:
            print(f"[MUSIC] Could not load {path}: {e}")

    def play_menu_music(self) -> None:
        """play menu/pause music."""
        if self.muted:
            return
        path = os.path.join(ASSETS, "menu_page_pause_page.mp3")
        if self._current_music_theme == "__menu__":
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
            self._current_music_theme = "__menu__"
        except Exception as e:
            print(f"[MUSIC] Could not load {path}: {e}")

    def play_game_over_music(self) -> None:
        if self.muted:
            return
        path = os.path.join(ASSETS, "game_over_page.mp3")
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.5)
            # pygame.mixer.music.play(0)   # play once
            pygame.mixer.music.play(-1)   # repeat
            self._current_music_theme = "__gameover__"
        except Exception as e:
            print(f"[MUSIC] Could not load {path}: {e}")

    def stop_music(self) -> None:
        pygame.mixer.music.stop()
        self._current_music_theme = None

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
        state = "muted" if self.muted else "unmuted"
        print(f"[SOUND] Volume {state}")
        return self.muted
