# Advanced Snake

A grid-based Snake game built with Python and Pygame. Everything is drawn with basic shapes — no external image or sound files.

## Run

```bash
cd snake-game
python -m venv venv
venv\Scripts\activate        # Windows
pip install pygame
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| Up / Down | Menu selection |
| Enter | Confirm menu choice |
| Arrow keys | Move |
| P / Escape | Pause / resume |
| R | Restart after game over |
| M | Mute (in-game) / Main menu (game over) |
| F1 | Debug overlay (live tuning) |
| M | Toggle sound mute |
| Escape (menu) | Quit |

## Architecture

The game is split into focused modules so gameplay systems stay decoupled:

| Module | Role |
|--------|------|
| `main.py` | Game loop, event routing, ties systems together |
| `src/constants.py` | Window size, colors, FPS |
| `src/config.py` | Default tuning values (speed, points, spawn rates) |
| `src/live_settings.py` | Runtime copies of config, adjusted via F1 overlay |
| `src/game_state.py` | PLAYING / PAUSED / DEAD states |
| `src/snake.py` | Grid movement, growth, direction |
| `src/food.py` | Normal food, color-match pairs, poison spawning |
| `src/world.py` | Theme palettes, maze walls, theme lifecycle |
| `src/portals.py` | Teleporter placement, teleport logic, cooldown |
| `src/physics.py` | Desert / ice / storm movement modifiers |
| `src/difficulty.py` | Score-tier feature gates |
| `src/shield.py` | Shield charges, invulnerability, color-fail streak |
| `src/scoring.py` | Session ID, per-run score and death stats |
| `src/save_manager.py` | JSON high score and last-10 run history |
| `src/ui.py` | HUD, overlays, game-over screen |
| `src/sound_manager.py` | Console sound hooks (no audio files) |
| `src/debug_overlay.py` | F1 stats panel and live hotkeys |
| `data/save.json` | Persistent save file (auto-created) |

**Data flow:** `main.py` reads input, asks `physics` for the next move direction, moves `snake`, checks `portals` and `food`, applies `shield` rules, updates `world` theme counters, and renders through `ui`. Death triggers `save_manager` to persist history.

## Difficulty Tiers

| Score | Unlocks |
|-------|---------|
| 0–50 | Normal food only |
| 51–100 | Color-match food (RED/BLUE pairs) |
| 101–150 | Ice slide and storm wind modifiers |
| 151+ | Poison tiles |

Press **F1 → T** to force a tier for testing.

## Sound

Sound hooks print to the terminal, e.g. `[SOUND EFFECT] Triggered: Eat`. Press **M** to mute.
