"""F1 debug overlay: live stats display and runtime tuning hotkeys."""

from __future__ import annotations

import pygame

from src.constants import COLOR_STORM_WARNING, COLOR_TEXT, WINDOW_HEIGHT, WINDOW_WIDTH
from src.difficulty import DifficultyManager
from src.live_settings import LiveSettings
from src.physics import PhysicsEngine
from src.portals import PortalManager
from src.snake import Snake
from src.stroop_colors import ball_count_for_score
from src.world import DESERT, FOREST, ICE, MAZE, STORM, World

HOTKEY_HELP = [
    "1/2  Move interval -/+ 25ms",
    "3/4  Portal cooldown -/+ 1",
    "5/6  Storm grace steps -/+ 1",
    "7    Cycle storm wind direction",
    "8    Reset storm gust counter",
    "9/0  Theme shift points -/+ 5",
    "T    Cycle force difficulty tier",
]


class DebugOverlay:
    def __init__(self) -> None:
        self.visible = False

    def toggle(self) -> None:
        self.visible = not self.visible

    def handle_key(
        self,
        key: int,
        live: LiveSettings,
        world: World,
        physics: PhysicsEngine,
        difficulty: DifficultyManager,
    ) -> bool:
        """Apply tuning hotkeys when overlay is open. Returns True if key was consumed."""
        if not self.visible:
            return False

        if key == pygame.K_t:
            difficulty.cycle_force_tier()
            return True

        if key == pygame.K_1:
            live.move_interval_ms -= 25
        elif key == pygame.K_2:
            live.move_interval_ms += 25
        elif key == pygame.K_3:
            live.portal_cooldown_steps -= 1
        elif key == pygame.K_4:
            live.portal_cooldown_steps += 1
        elif key == pygame.K_5:
            live.storm_grace_steps -= 1
        elif key == pygame.K_6:
            live.storm_grace_steps += 1
        elif key == pygame.K_7:
            self._cycle_storm_wind(world)
        elif key == pygame.K_8:
            physics.on_storm_entered()
        elif key == pygame.K_9:
            live.theme_shift_points -= 5
        elif key == pygame.K_0:
            live.theme_shift_points += 5
        else:
            return False

        live.clamp()
        return True

    def _cycle_storm_wind(self, world: World) -> None:
        order = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        if world.storm_wind_direction in order:
            idx = (order.index(world.storm_wind_direction) + 1) % len(order)
            world.storm_wind_direction = order[idx]
        else:
            world.storm_wind_direction = order[0]

    def _active_modifiers(
        self,
        world: World,
        physics: PhysicsEngine,
        live: LiveSettings,
        difficulty: DifficultyManager,
        score: int,
        now_ms: int,
    ) -> list[str]:
        mods: list[str] = []
        theme = world.active_theme

        if theme == FOREST:
            mods.append("Forest: baseline speed")
        elif theme == DESERT:
            if physics.held_arrows:
                mods.append(f"Desert: keys held ({live.move_interval_ms}ms)")
            else:
                slow = live.move_interval_ms * live.desert_slow_multiplier
                mods.append(f"Desert: keys released ({slow}ms)")
        elif theme == ICE:
            if not difficulty.ice_storm_active(score):
                mods.append("Ice: theme only (press locked)")
            elif physics.ice_steps_remaining > 0:
                mods.append(f"Ice: burst steps ({physics.ice_steps_remaining} left)")
            else:
                mods.append("Ice: press arrow to move (3 steps)")
        elif theme == STORM:
            if not difficulty.ice_storm_active(score):
                mods.append("Storm: theme only (wind locked)")
            elif world.storm_grace_steps_remaining > 0:
                mods.append(f"Storm: grace ({world.storm_grace_steps_remaining} steps)")
            elif physics.storm_gusts_left() > 0:
                mods.append(
                    f"Storm: {physics.storm_gusts_left()} gust(s) left ({world.storm_wind_label})"
                )
            else:
                mods.append("Storm: gusts finished — normal control")
        elif theme == MAZE:
            mods.append("Maze: wall pillars active")

        if world.storm_is_approaching():
            mods.append("Forecast: storm approaching")

        return mods

    def build_info_lines(
        self,
        snake: Snake,
        world: World,
        physics: PhysicsEngine,
        portals: PortalManager,
        live: LiveSettings,
        difficulty: DifficultyManager,
        score: int,
        now_ms: int,
    ) -> list[str]:
        hx, hy = snake.head
        lines = [
            "=== DEBUG OVERLAY (F1) ===",
            f"Head grid: ({hx}, {hy})  Dir: {snake.direction}",
            f"Body length: {len(snake.body)}  Grow queue: {snake.grow_pending}",
            "",
            "— Difficulty —",
            f"Score tier: {difficulty.tier_label(score)}",
            f"Force tier: {difficulty.force_tier_label()}",
            f"Stroop balls: {ball_count_for_score(score)}",
            f"Color match: {difficulty.color_match_active(score)}",
            f"Ice/Storm mods: {difficulty.ice_storm_active(score)}",
            f"Poison spawn: {difficulty.poison_active(score)}",
            "",
            "— Theme —",
            f"Active: {world.label}",
            f"Points since shift: {world.points_since_theme_change}/{live.theme_shift_points}",
            f"Next shift in: {world.points_until_shift()} pts",
            f"Pending theme: {world.pending_theme or '—'}",
            "",
            "— Storm —",
            f"Wind: {world.storm_wind_label}",
            f"Gusts left: {physics.storm_gusts_left()}",
            f"Grace steps left: {world.storm_grace_steps_remaining}",
            f"Speed boost: {physics.is_speed_boost_active(now_ms)}",
            "",
            "— Portals —",
            f"State: {portals.visibility_label()}",
            f"Entrance: {portals.entrance}  Exit: {portals.exit}",
            f"Cooldown: {portals.cooldown_steps_remaining()} steps",
            f"Phase change in: {portals.ms_until_phase_change(now_ms) / 1000:.1f}s",
            "",
            "— Active modifiers —",
        ]
        mods = self._active_modifiers(world, physics, live, difficulty, score, now_ms)
        lines.extend(mods if mods else ["(none)"])
        lines.extend([
            "",
            "— Live settings —",
            f"Move interval: {live.move_interval_ms} ms",
            f"Portal cooldown: {live.portal_cooldown_steps} steps",
            f"Storm grace: {live.storm_grace_steps} steps",
            f"Theme shift at: {live.theme_shift_points} pts",
            f"Desert slow x: {live.desert_slow_multiplier}",
            f"Ice press steps: {live.ice_press_steps}",
            "",
            "— Hotkeys (overlay open) —",
        ])
        lines.extend(HOTKEY_HELP)
        return lines

    def draw(
        self,
        screen: pygame.Surface,
        snake: Snake,
        world: World,
        physics: PhysicsEngine,
        portals: PortalManager,
        live: LiveSettings,
        difficulty: DifficultyManager,
        score: int,
        now_ms: int,
    ) -> None:
        if not self.visible:
            return

        panel_w = 360
        panel_h = WINDOW_HEIGHT - 20
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 10, 20, 220))

        font = pygame.font.Font(None, 22)
        y = 10
        for line in self.build_info_lines(snake, world, physics, portals, live, difficulty, score, now_ms):
            color = COLOR_TEXT
            if line.startswith("==="):
                color = COLOR_STORM_WARNING
            surf = font.render(line, True, color)
            panel.blit(surf, (10, y))
            y += 20

        screen.blit(panel, (WINDOW_WIDTH - panel_w - 10, 10))
