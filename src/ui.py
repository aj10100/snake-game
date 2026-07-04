"""On-screen text: HUD, pause overlay, and game-over summary."""

from __future__ import annotations

from typing import Any

import pygame

from src import game_state
from src.constants import (
    CELL_SIZE,
    COLOR_BACKGROUND,
    COLOR_FOOD,
    COLOR_GAME_OVER,
    COLOR_HUD_PANEL,
    COLOR_INVULN_FLASH,
    COLOR_MAZE_WALL,
    COLOR_NEW_RECORD,
    COLOR_POISON,
    COLOR_STORM_BALL,
    COLOR_PORTAL_COOLDOWN,
    COLOR_PORTAL_ENTRANCE,
    COLOR_PORTAL_EXIT,
    COLOR_SNAKE_BODY,
    COLOR_SNAKE_HEAD,
    COLOR_STORM_WARNING,
    COLOR_TEXT,
    HUD_HEIGHT,
    PLAYFIELD_Y,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from src.difficulty import DifficultyManager
from src.food import Food
from src.physics import PhysicsEngine
from src.portals import PortalManager
from src.scoring import DEATH_LABELS, RunStats, Session
from src.shield import ShieldState
from src.snake import Snake
from src.stroop_colors import stroop_label, stroop_rgb
from src.world import STORM, World

MENU_ITEMS = ["Play Game", "Reset Data", "Quit"]


def draw_main_menu(screen: pygame.Surface, selected: int, high_score: int) -> None:
    screen.fill(COLOR_BACKGROUND)

    center_x = WINDOW_WIDTH // 2

    title_font = pygame.font.Font(None, 80)
    title = title_font.render("Advanced Snake", True, COLOR_SNAKE_HEAD)
    screen.blit(title, title.get_rect(center=(center_x, 110)))

    tag_font = pygame.font.Font(None, 28)
    tagline = tag_font.render("Stroop Colors  |  Portals  |  Shields  |  Themes", True, COLOR_TEXT)
    screen.blit(tagline, tagline.get_rect(center=(center_x, 158)))

    score_font = pygame.font.Font(None, 36)
    score_surf = score_font.render(f"High Score: {high_score}", True, COLOR_STORM_WARNING)
    screen.blit(score_surf, score_surf.get_rect(center=(center_x, 205)))

    item_font = pygame.font.Font(None, 44)
    start_y = 280
    for index, label in enumerate(MENU_ITEMS):
        is_selected = index == selected
        color = COLOR_STORM_WARNING if is_selected else COLOR_TEXT
        prefix = "> " if is_selected else "   "
        surf = item_font.render(f"{prefix}{label}", True, color)
        screen.blit(surf, surf.get_rect(center=(center_x, start_y + index * 52)))

    hint_font = pygame.font.Font(None, 24)
    hints = [
        "Up / Down — Select",
        "Enter — Confirm",
        "Escape — Quit",
    ]
    y = WINDOW_HEIGHT - 110
    for line in hints:
        surf = hint_font.render(line, True, COLOR_TEXT)
        screen.blit(surf, surf.get_rect(center=(center_x, y)))
        y += 26

    ctrl_font = pygame.font.Font(None, 22)
    ctrl = ctrl_font.render(
        "In-game: Arrows move  |  P pause  |  F1 debug  |  M mute",
        True,
        (160, 160, 170),
    )
    screen.blit(ctrl, ctrl.get_rect(center=(center_x, WINDOW_HEIGHT - 28)))


def draw_grid(
    screen: pygame.Surface,
    grid_width: int,
    grid_height: int,
    grid_line_color: tuple[int, int, int],
) -> None:
    for x in range(grid_width + 1):
        pygame.draw.line(
            screen,
            grid_line_color,
            (x * CELL_SIZE, PLAYFIELD_Y),
            (x * CELL_SIZE, WINDOW_HEIGHT),
        )
    for y in range(grid_height + 1):
        pygame.draw.line(
            screen,
            grid_line_color,
            (0, PLAYFIELD_Y + y * CELL_SIZE),
            (WINDOW_WIDTH, PLAYFIELD_Y + y * CELL_SIZE),
        )


def draw_cell(screen: pygame.Surface, grid_pos: tuple[int, int], color: tuple[int, int, int]) -> None:
    x, y = grid_pos
    rect = pygame.Rect(
        x * CELL_SIZE + 1,
        PLAYFIELD_Y + y * CELL_SIZE + 1,
        CELL_SIZE - 2,
        CELL_SIZE - 2,
    )
    pygame.draw.rect(screen, color, rect)


def _draw_portal(
    screen: pygame.Surface,
    grid_pos: tuple[int, int],
    color: tuple[int, int, int],
    on_cooldown: bool,
) -> None:
    x, y = grid_pos
    cx = x * CELL_SIZE + CELL_SIZE // 2
    cy = PLAYFIELD_Y + y * CELL_SIZE + CELL_SIZE // 2
    radius = CELL_SIZE // 2 - 2
    draw_color = COLOR_PORTAL_COOLDOWN if on_cooldown else color
    pygame.draw.circle(screen, draw_color, (cx, cy), radius)
    pygame.draw.circle(screen, COLOR_TEXT, (cx, cy), radius, 1)


def draw_playfield(
    screen: pygame.Surface,
    snake: Snake,
    food: Food,
    world: World,
    portals: PortalManager,
    grid_width: int,
    grid_height: int,
    shield: ShieldState,
    now_ms: int,
) -> None:
    screen.fill(COLOR_HUD_PANEL, (0, 0, WINDOW_WIDTH, HUD_HEIGHT))
    screen.fill(world.background_color, (0, PLAYFIELD_Y, WINDOW_WIDTH, WINDOW_HEIGHT - PLAYFIELD_Y))
    draw_grid(screen, grid_width, grid_height, world.grid_line_color)

    for wall in world.maze_walls:
        draw_cell(screen, wall, COLOR_MAZE_WALL)

    if portals.visible and portals.entrance is not None:
        _draw_portal(screen, portals.entrance, COLOR_PORTAL_ENTRANCE, portals.is_on_cooldown())
    if portals.visible and portals.exit is not None:
        _draw_portal(screen, portals.exit, COLOR_PORTAL_EXIT, portals.is_on_cooldown())

    if food.position is not None:
        draw_cell(screen, food.position, COLOR_FOOD)

    for color_key, pos in food.color_items.items():
        draw_cell(screen, pos, stroop_rgb(color_key))

    if food.poison_position is not None:
        draw_cell(screen, food.poison_position, COLOR_POISON)

    if food.storm_ball_position is not None:
        x, y = food.storm_ball_position
        cx = x * CELL_SIZE + CELL_SIZE // 2
        cy = PLAYFIELD_Y + y * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(screen, COLOR_STORM_BALL, (cx, cy), CELL_SIZE // 2 - 2)
        pygame.draw.circle(screen, (80, 80, 80), (cx, cy), CELL_SIZE // 2 - 2, 1)

    flash_invuln = shield.is_invulnerable() and (now_ms // 120) % 2 == 0
    for index, segment in enumerate(snake.body):
        if index == 0:
            color = COLOR_INVULN_FLASH if flash_invuln else COLOR_SNAKE_HEAD
        else:
            color = COLOR_SNAKE_BODY
        draw_cell(screen, segment, color)


def draw_color_target(screen: pygame.Surface, food: Food) -> None:
    if food.mode != "color":
        return

    word = stroop_label(food.target_color_key)
    ink = food.stroop_ink_rgb

    font = pygame.font.Font(None, 22)
    label = font.render(word, True, ink)
    hint_font = pygame.font.Font(None, 16)
    hint = hint_font.render("word", True, (150, 150, 160))
    x = WINDOW_WIDTH - label.get_width() - hint.get_width() - 16
    screen.blit(label, (x, 8))
    screen.blit(hint, (x + label.get_width() + 4, 12))


def draw_hud(
    screen: pygame.Surface,
    run_stats: RunStats,
    now_ms: int,
    world: World,
) -> None:
    font = pygame.font.Font(None, 20)
    text = (
        f"Score {run_stats.score}  |  {world.label}  |  "
        f"{run_stats.survival_seconds(now_ms):.1f}s"
    )
    screen.blit(font.render(text, True, COLOR_TEXT), (8, 5))


def draw_new_record_popup(screen: pygame.Surface, score: int, now_ms: int) -> None:
    """Centered popup when the run beats the saved high score."""
    center_x = WINDOW_WIDTH // 2
    center_y = PLAYFIELD_Y + (WINDOW_HEIGHT - PLAYFIELD_Y) // 2

    box_w, box_h = 320, 100
    box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box.fill((20, 20, 35, 230))
    pygame.draw.rect(box, COLOR_NEW_RECORD, (0, 0, box_w, box_h), 2, border_radius=6)

    pulse = 1.0 + 0.06 * abs((now_ms % 500) / 250.0 - 1.0)
    title_font = pygame.font.Font(None, int(44 * pulse))
    title = title_font.render("NEW HIGH SCORE!", True, COLOR_NEW_RECORD)
    box.blit(title, title.get_rect(center=(box_w // 2, 36)))

    score_font = pygame.font.Font(None, 32)
    score_surf = score_font.render(str(score), True, COLOR_TEXT)
    box.blit(score_surf, score_surf.get_rect(center=(box_w // 2, 72)))

    screen.blit(box, (center_x - box_w // 2, center_y - box_h // 2))


def draw_storm_alert(screen: pygame.Surface, world: World, now_ms: int) -> None:
    if not world.is_storm_alert_active(now_ms):
        return

    remaining_s = max(0.0, (world.storm_alert_until_ms - now_ms) / 1000.0)
    grace = world.storm_grace_steps_remaining

    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    pulse = 120 + int(40 * abs((now_ms // 250) % 2 - 0.5) * 2)
    overlay.fill((40, 40, 80, pulse))
    screen.blit(overlay, (0, 0))

    center_x = WINDOW_WIDTH // 2
    title_font = pygame.font.Font(None, 64)
    title = title_font.render("STORM WARNING", True, COLOR_STORM_WARNING)
    screen.blit(title, title.get_rect(center=(center_x, WINDOW_HEIGHT // 2 - 50)))

    body_font = pygame.font.Font(None, 32)
    lines = [
        f"Wind direction: {world.storm_wind_label}",
        f"Winds begin in {grace} steps",
        f"Alert ends in {remaining_s:.1f}s",
        "Snake frozen — plan your route",
    ]
    y = WINDOW_HEIGHT // 2
    for line in lines:
        surface = body_font.render(line, True, COLOR_TEXT)
        screen.blit(surface, surface.get_rect(center=(center_x, y)))
        y += 36


def draw_storm_grace_hint(
    screen: pygame.Surface,
    world: World,
    physics: PhysicsEngine,
    now_ms: int,
) -> None:
    """Small reminder while storm grace steps remain after the main alert fades."""
    if world.active_theme != STORM or world.is_storm_alert_active(now_ms):
        return
    if world.storm_grace_steps_remaining <= 0:
        return

    font = pygame.font.Font(None, 28)
    text = font.render(
        f"Storm winds in {world.storm_grace_steps_remaining} steps ({world.storm_wind_label})",
        True,
        COLOR_STORM_WARNING,
    )
    screen.blit(text, text.get_rect(midtop=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 36)))


def draw_pause_overlay(screen: pygame.Surface) -> None:
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    title_font = pygame.font.Font(None, 56)
    title = title_font.render("PAUSED", True, COLOR_TEXT)
    screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)))

    hint_font = pygame.font.Font(None, 28)
    hint = hint_font.render("Press P or Escape to resume", True, COLOR_TEXT)
    screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 24)))


def _death_cause_label(cause: str | None) -> str:
    if cause is None:
        return "—"
    return DEATH_LABELS.get(cause, cause.replace("_", " ").title())


def _draw_history_table(
    screen: pygame.Surface,
    history: list[dict[str, Any]],
    current_score: int,
    start_y: int,
) -> int:
    font = pygame.font.Font(None, 22)
    header_font = pygame.font.Font(None, 24)
    header = header_font.render("Last 10 Runs", True, COLOR_STORM_WARNING)
    screen.blit(header, header.get_rect(center=(WINDOW_WIDTH // 2, start_y)))
    y = start_y + 28

    col_x = [WINDOW_WIDTH // 2 - 200, WINDOW_WIDTH // 2 - 60, WINDOW_WIDTH // 2 + 50, WINDOW_WIDTH // 2 + 140]
    for label, x in zip(["Score", "Time", "Cause", "Session"], col_x):
        screen.blit(font.render(label, True, COLOR_TEXT), (x, y))
    y += 22

    if not history:
        empty = font.render("(no history yet)", True, COLOR_TEXT)
        screen.blit(empty, empty.get_rect(center=(WINDOW_WIDTH // 2, y + 12)))
        return y + 30

    for index, entry in enumerate(history[:10]):
        score = int(entry.get("score", 0))
        row_color = COLOR_NEW_RECORD if score == current_score and index == 0 else COLOR_TEXT
        row = [
            str(score),
            f"{float(entry.get('survival_seconds', 0)):.1f}s",
            _death_cause_label(entry.get("death_cause")),
            str(entry.get("session_id", "—"))[:8],
        ]
        for text, x in zip(row, col_x):
            screen.blit(font.render(text, True, row_color), (x, y))
        y += 20
    return y


def draw_game_over(
    screen: pygame.Surface,
    session: Session,
    run_stats: RunStats,
    now_ms: int,
    high_score: int,
    new_record: bool,
    world: World,
    save_data: dict[str, Any],
) -> None:
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    screen.blit(overlay, (0, 0))

    center_x = WINDOW_WIDTH // 2
    y = 36

    title_font = pygame.font.Font(None, 56)
    title = title_font.render("Game Over", True, COLOR_GAME_OVER)
    screen.blit(title, title.get_rect(center=(center_x, y)))
    y += 48

    if new_record:
        banner_font = pygame.font.Font(None, 40)
        banner = banner_font.render("NEW RECORD!", True, COLOR_NEW_RECORD)
        screen.blit(banner, banner.get_rect(center=(center_x, y)))
        y += 36

    body_font = pygame.font.Font(None, 26)
    summary = [
        f"Score: {run_stats.score}   |   High Score: {high_score}",
        f"Survived: {run_stats.survival_seconds(now_ms):.1f}s",
        f"Terminal theme: {world.label}",
        f"Cause: {run_stats.death_label()}",
        f"Session ID: {session.session_id}",
    ]
    for line in summary:
        surface = body_font.render(line, True, COLOR_TEXT)
        screen.blit(surface, surface.get_rect(center=(center_x, y)))
        y += 28

    history = save_data.get("history", [])
    y = _draw_history_table(screen, history, run_stats.score, y + 12)

    hint_font = pygame.font.Font(None, 24)
    hint = hint_font.render("Press R to restart  |  H main menu  |  M mute  |  Escape quit", True, COLOR_TEXT)
    screen.blit(hint, hint.get_rect(center=(center_x, min(y + 24, WINDOW_HEIGHT - 20))))
