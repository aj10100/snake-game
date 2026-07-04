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

MENU_ITEMS = ["start", "precautions", "reset record", "quit"]


def draw_main_menu(screen, selected, high_score, assets):
    # full-screen background image
    screen.blit(assets["start_page"], (0, 0))

    # # semi-transparent dark panel behind the menu items
    # panel = pygame.Surface((400, 360), pygame.SRCALPHA)
    # panel.fill((10, 10, 20, 180))
    # panel_x = WINDOW_WIDTH // 2 - 200
    # panel_y = 80
    # screen.blit(panel, (panel_x, panel_y))

    center_x = WINDOW_WIDTH // 2
    # title
    title = assets["font_menu_title"].render("Classic Snake", True, (94, 23, 1)) #2, 31, 18
    screen.blit(title, title.get_rect(center=(center_x, 140)))

    # high score
    score_surf = assets["font_body"].render(f"High Score: {high_score}", True, (255, 200, 80))
    screen.blit(score_surf, score_surf.get_rect(center=(center_x, 200)))

    # menu items
    start_y = 250
    for index, label in enumerate(MENU_ITEMS):
        is_selected = index == selected
        color = (255, 200, 80) if is_selected else (200, 200, 210)
        prefix = "> " if is_selected else "   "
        surf = assets["font_menu_item"].render(f"{prefix}{label}", True, color)
        screen.blit(surf, surf.get_rect(center=(center_x, start_y + index * 48)))

    # hints at the bottom
    hints = ["Up / Down — Select", "Enter — Confirm", "Escape — Quit"]
    y = WINDOW_HEIGHT - 100
    for line in hints:
        surf = assets["font_body"].render(line, True, (180, 180, 190))
        screen.blit(surf, surf.get_rect(center=(center_x, y)))
        y += 24

    ctrl = assets["font_hud"].render(
        "In-game: Arrows move  |  P pause  |  M mute", True, (140, 140, 150)
    )
    screen.blit(ctrl, ctrl.get_rect(center=(center_x, WINDOW_HEIGHT - 24)))

def draw_precautions(screen: pygame.Surface, assets: dict,) -> None:
    screen.blit(assets["high_score_finish"], (0, 0))
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))
    center_x = WINDOW_WIDTH // 2

    title_font = assets["font_menu_title"]
    title = title_font.render("Precautions", True, COLOR_STORM_WARNING)
    screen.blit(title, title.get_rect(center=(center_x, 60)))

    body_font = assets["font_menu_item"]
    lines = [
        "There are 4 worlds:",
        "",
        "  Forest",
        "  Desert",
        "  Glacier",
        "  Clouds / Cyclone",
        "",
        "they come with your actions but quite randomly .",
        "",
         "Feel free to explore ",

    ]
    y = 120
    for line in lines:
        surf = body_font.render(line, True, COLOR_TEXT)
        screen.blit(surf, surf.get_rect(center=(center_x, y)))
        y += 32

    hint_font = assets["font_menu_hint"]
    hint = hint_font.render("Press Escape or Enter to go back", True, COLOR_TEXT)
    screen.blit(hint, hint.get_rect(center=(center_x, WINDOW_HEIGHT - 40)))


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

def draw_wrong_color_warning(screen: pygame.Surface, consecutive: int, assets: dict,) -> None:
    if consecutive <= 0:
        return
    font = assets["font_body"]
    color = COLOR_GAME_OVER if consecutive >= 2 else COLOR_STORM_WARNING
    text = font.render(f"Wrong color: {consecutive}/3", True, color)
    screen.blit(text, text.get_rect(midtop=(WINDOW_WIDTH // 2, PLAYFIELD_Y + 6)))

def draw_storm_warning(screen: pygame.Surface, msg: str, now_ms: int, assets: dict,) -> None:
    if not msg:
        return
    font = assets["font_body"]
    color = COLOR_GAME_OVER if (now_ms // 400) % 2 == 0 else COLOR_STORM_WARNING
    surf = font.render(msg, True, color)
    screen.blit(surf, surf.get_rect(midbottom=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 8)))


def draw_cell(screen: pygame.Surface, grid_pos: tuple[int, int], color: tuple[int, int, int],) -> None:
    x, y = grid_pos
    rect = pygame.Rect(
        x * CELL_SIZE + 1,
        PLAYFIELD_Y + y * CELL_SIZE + 1,
        CELL_SIZE - 2,
        CELL_SIZE - 2,
    )
    pygame.draw.rect(screen, color, rect)


# def _draw_portal(
#     screen: pygame.Surface,
#     grid_pos: tuple[int, int],
#     color: tuple[int, int, int],
#     on_cooldown: bool,
# ) -> None:
#     x, y = grid_pos
#     cx = x * CELL_SIZE + CELL_SIZE // 2
#     cy = PLAYFIELD_Y + y * CELL_SIZE + CELL_SIZE // 2
#     radius = CELL_SIZE // 2 - 2
#     draw_color = COLOR_PORTAL_COOLDOWN if on_cooldown else color
#     pygame.draw.circle(screen, draw_color, (cx, cy), radius)
#     pygame.draw.circle(screen, COLOR_TEXT, (cx, cy), radius, 1)


def _blit_sprite(screen, sprite, grid_pos):
    x, y = grid_pos
    screen.blit(sprite, (x * CELL_SIZE, PLAYFIELD_Y + y * CELL_SIZE))

def _blit_sprite_centered(screen, sprite, grid_pos):
    x, y = grid_pos
    cx = x * CELL_SIZE + CELL_SIZE // 2
    cy = PLAYFIELD_Y + y * CELL_SIZE + CELL_SIZE // 2
    rect = sprite.get_rect(center=(cx, cy))
    screen.blit(sprite, rect)

def draw_playfield(screen, snake, food, world, portals, grid_width, grid_height, shield, now_ms, assets):
    # hud strip
    screen.fill(COLOR_HUD_PANEL, (0, 0, WINDOW_WIDTH, HUD_HEIGHT))

    # theme background image
    theme_bg_key = f"bg_{world.active_theme}"
    if theme_bg_key in assets:
        screen.blit(assets[theme_bg_key], (0, PLAYFIELD_Y))
    else:
        screen.fill(world.background_color, (0, PLAYFIELD_Y, WINDOW_WIDTH, WINDOW_HEIGHT - PLAYFIELD_Y))

    # draw_grid(screen, grid_width, grid_height, world.grid_line_color)
    grid_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT - PLAYFIELD_Y), pygame.SRCALPHA)
    grid_surf.fill((0, 0, 0, 0))
    grid_color = (*world.grid_line_color, 60)
    for x in range(grid_width + 1):
        pygame.draw.line(grid_surf, grid_color, (x * CELL_SIZE, 0), (x * CELL_SIZE, WINDOW_HEIGHT - PLAYFIELD_Y))
    for y in range(grid_height + 1):
        pygame.draw.line(grid_surf, grid_color, (0, y * CELL_SIZE), (WINDOW_WIDTH, y * CELL_SIZE))
    screen.blit(grid_surf, (0, PLAYFIELD_Y))

    # maze walls
    for wall in world.maze_walls:
        draw_cell(screen, wall, COLOR_MAZE_WALL)

    # portals
    if portals.visible and portals.entrance is not None:
        _blit_sprite_centered(screen, assets["entry_portal"], portals.entrance)
    if portals.visible and portals.exit is not None:
        _blit_sprite_centered(screen, assets["exit_portal"],  portals.exit)

    # food
    if food.position is not None:
        sprite_key = "food_red"      # default
        if food.mode == "poison":
            sprite_key = "food_violet"
        elif food.mode == "color":
            sprite_key = "food_green"
        _blit_sprite_centered(screen, assets[sprite_key], food.position)

    # stroop color-match items
    for color_key, pos in food.color_items.items():
        sprite_key = f"stroop_{color_key}"
        if sprite_key in assets:
            _blit_sprite_centered(screen, assets[sprite_key], pos)
        else:
            draw_cell(screen, pos, stroop_rgb(color_key))

    # poison item
    if food.poison_position is not None:
        _blit_sprite_centered(screen, assets["poison"], food.poison_position)

    if food.storm_ball_position is not None:
        _blit_sprite_centered(screen, assets["poison"], food.storm_ball_position)

    # nnake — head, body, tail sprites;
    shielded = shield.charges >0
    for index, segment in enumerate(snake.body):
        if index == 0:
            key = "shield_head" if shielded else "snake_head"
        elif index == len(snake.body) - 1:
            key = "tail_shield" if shielded else "snake_tail"
        else:
            key = "shield_body" if shielded else "snake_body"
        _blit_sprite(screen, assets[key], segment)


def draw_color_target(screen: pygame.Surface, food: Food, assets: dict,) -> None:
    if food.mode != "color":
        return

    word = stroop_label(food.target_color_key)
    ink = food.stroop_ink_rgb

    font = assets["font_hud"]
    label = font.render(word, True, ink)
    x = WINDOW_WIDTH - label.get_width() - 10
    screen.blit(label, (x, 8))


def draw_hud(screen, run_stats, now_ms, world, assets):
    text = (
        f"Score {run_stats.score}  |  "
        f"{run_stats.survival_seconds(now_ms):.1f}s  |  "
        f"{world.label}"
    )
    screen.blit(assets["font_hud"].render(text, True, COLOR_TEXT), (8, 4))


def draw_new_record_popup(screen: pygame.Surface, score: int, now_ms: int, assets: dict,) -> None:
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




def draw_pause_overlay(screen: pygame.Surface, assets: dict,) -> None:
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    title_font = assets["font_big"]
    title = title_font.render("PAUSED", True, COLOR_TEXT)
    screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)))

    hint_font = assets["font_body"]
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
    save_data: dict[str, Any], assets: dict,
) -> None:

    bg_key = "high_score_finish" if new_record else "finish_game"
    screen.blit(assets[bg_key], (0, 0))
    # Darken so text is readable
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 155))
    screen.blit(overlay, (0, 0))
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)


    center_x = WINDOW_WIDTH // 2
    y = 36

    title_font = assets["font_big"]
    title = title_font.render("Game Over", True, COLOR_GAME_OVER)
    screen.blit(title, title.get_rect(center=(center_x, y)))
    y += 48

    if new_record:
        banner_font = assets["font_menu_item"]
        banner = banner_font.render("NEW RECORD!", True, COLOR_NEW_RECORD)
        screen.blit(banner, banner.get_rect(center=(center_x, y)))
        y += 36

    body_font = assets["font_body"]
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

    hint_font = assets["font_menu_hint"]
    hint = hint_font.render("Press R to restart  |  H main menu  |  M mute  |  Escape quit", True, COLOR_TEXT)
    screen.blit(hint, hint.get_rect(center=(center_x, min(y + 24, WINDOW_HEIGHT - 20))))
