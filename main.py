"""Advanced Snake — entry point and main game loop."""

import random
import sys
from typing import Any

import pygame

from src import game_state
from src.config import STORM_BALL_HIDDEN_MAX_MS, STORM_BALL_HIDDEN_MIN_MS
from src.constants import GRID_HEIGHT, GRID_WIDTH, TARGET_FPS, WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH, CELL_SIZE, HUD_HEIGHT
from src.difficulty import DifficultyManager
from src.food import Food
from src.physics import PhysicsEngine , collides_after_move, head_in_collision_zone
from src.portals import PortalManager
from src.save_manager import get_high_score, load_save, record_run, reset_all_save
from src.scoring import DEATH_COLOR_FAIL, DEATH_POISON, DEATH_SELF, DEATH_WALL, RunStats, Session
DEATH_STORM = "storm"
from src.shield import ShieldState
from src.snake import Snake
from src.sound_manager import (
    SFX_DIE,
    SFX_EAT,
    SFX_OPTION_CHOOSE,
    SFX_POISON,
    SFX_RECORD,
    SFX_SHIELD_GAIN,
    SFX_SHIELD_LOSS,
    SFX_TELEPORT,
    SFX_TELEPORT_OUT,
    SFX_MOVE_CLOUD,
    SFX_MOVE_GLACIER,
    SoundManager,
)
from src.ui import (
    MENU_ITEMS,
    draw_color_target,
    draw_game_over,
    draw_hud,
    draw_main_menu,
    draw_new_record_popup,
    draw_pause_overlay,
    draw_playfield,
    draw_precautions,
    draw_storm_warning,
    draw_wrong_color_warning,
)
from src.world import STORM, World

ARROW_KEY_MAP = {
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
}


def blocked_spawn_cells(snake: Snake, world: World, portals: PortalManager) -> list[tuple[int, int]]:
    return list(snake.body) + list(world.blocked_cells()) + list(portals.blocked_cells())


def spawn_food(food: Food, snake: Snake, world: World, portals: PortalManager, difficulty: DifficultyManager, score: int) -> None:
    food.spawn(blocked_spawn_cells(snake, world, portals), difficulty, score, snake)


def reset_run(
    snake: Snake,
    food: Food,
    run_stats: RunStats,
    world: World,
    physics: PhysicsEngine,
    portals: PortalManager,
    difficulty: DifficultyManager,
    shield: ShieldState,
    now_ms: int,
) -> int:
    snake.__init__()
    world.reset()
    physics.reset()
    portals.reset(now_ms)
    shield.reset()
    food.clear()
    food.storm_ball_phase_end_ms = now_ms + random.randint(STORM_BALL_HIDDEN_MIN_MS, STORM_BALL_HIDDEN_MAX_MS)
    spawn_food(food, snake, world, portals, difficulty, 0)
    run_stats.start_run(now_ms)
    return now_ms


def handle_theme_change(prev_theme: str | None, world: World, physics: PhysicsEngine, sound) -> None:
    sound.play_theme_music(world.active_theme)
    # pass  # no automatic storm wind setup needed anymore

def handle_events(
    state: str,
    snake: Snake,
    food: Food,
    run_stats: RunStats,
    world: World,
    physics: PhysicsEngine,
    portals: PortalManager,

    difficulty: DifficultyManager,
    shield: ShieldState,
    sound: SoundManager,
    menu_selection: int,
    save_data: dict[str, Any],
    session: Session,
    now_ms: int,
) -> tuple[bool, str, int | None, int]:
    new_state = state
    move_reset: int | None = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, new_state, move_reset, menu_selection

        if event.type == pygame.WINDOWFOCUSLOST and new_state == game_state.PLAYING:
            new_state = game_state.PAUSED
            continue

        if event.type == pygame.KEYDOWN:
            if new_state == game_state.MENU:
                if event.key == pygame.K_UP:
                    menu_selection = (menu_selection - 1) % len(MENU_ITEMS)
                    sound.play(SFX_OPTION_CHOOSE)
                elif event.key == pygame.K_DOWN:
                    menu_selection = (menu_selection + 1) % len(MENU_ITEMS)
                    sound.play(SFX_OPTION_CHOOSE)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    sound.play(SFX_OPTION_CHOOSE)
                    if menu_selection == 0:
                        move_reset = reset_run(snake, food, run_stats, world, physics, portals, difficulty, shield, now_ms)
                        sound.play_theme_music(world.active_theme)
                        new_state = game_state.PLAYING
                    elif menu_selection == 1:
                        new_state = game_state.PRECAUTIONS
                    elif menu_selection == 2:
                        reset_all_save(save_data)
                        session.session_high_score = 0
                    else:
                        return False, new_state, move_reset, menu_selection
                elif event.key == pygame.K_ESCAPE:
                    return False, new_state, move_reset, menu_selection
                continue

            if event.key == pygame.K_m:
                sound.toggle_mute()
                continue



            if new_state == game_state.DEAD and event.key == pygame.K_h:
                new_state = game_state.MENU
                continue


            key_name = ARROW_KEY_MAP.get(event.key)

            if new_state == game_state.PAUSED:
                if event.key in (pygame.K_p, pygame.K_ESCAPE):
                    new_state = game_state.PLAYING
                continue

            if new_state == game_state.PRECAUTIONS:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    new_state = game_state.MENU
                continue

            if event.key == pygame.K_ESCAPE:
                return False, new_state, move_reset, menu_selection

            if new_state == game_state.PLAYING:
                if event.key == pygame.K_p:
                    new_state = game_state.PAUSED
                elif event.key == pygame.K_F2:
                    prev_theme = world.active_theme
                    world.enter_storm(now_ms)
                    handle_theme_change(prev_theme, world, physics,sound)
                elif key_name is not None:
                    physics.on_key_down(key_name, run_stats.score)
                    snake.set_direction_from_key(key_name)

            if new_state == game_state.DEAD and event.key == pygame.K_r:
                sound.play_theme_music(world.active_theme)
                move_reset = reset_run(
                    snake, food, run_stats, world, physics, portals, difficulty, shield, now_ms
                )
                new_state = game_state.PLAYING

        elif event.type == pygame.KEYUP and new_state == game_state.PLAYING:
            key_name = ARROW_KEY_MAP.get(event.key)
            if key_name is not None:
                physics.on_key_up(key_name)

    return True, new_state, move_reset, menu_selection


def process_food_eat(
    food: Food,
    snake: Snake,
    run_stats: RunStats,
    world: World,
    physics: PhysicsEngine,
    portals: PortalManager,
    difficulty: DifficultyManager,
    shield: ShieldState,
    sound: SoundManager,
    now_ms: int,
) -> str | None:
    if not food.is_at(snake.head):
        return None

    eat_kind, point_delta = food.handle_eat(snake.head)

    if eat_kind == "storm_ball":
        sound.play(SFX_POISON)
        if physics.storm_mode == "speed":
            run_stats.record_death(DEATH_STORM, now_ms)
            return game_state.DEAD
        if world.active_theme == STORM and physics.storm_poison_count >= 1:
            run_stats.record_death(DEATH_STORM, now_ms)
            return game_state.DEAD
        prev_theme = world.active_theme
        world.enter_storm(now_ms)
        physics.enter_storm_frozen()
        return None

    if eat_kind == "poison":
        sound.play(SFX_POISON)
        if physics.storm_mode == "speed":
            run_stats.record_death(DEATH_POISON, now_ms)
            return game_state.DEAD
        block = shield.try_block_poison()
        if block is not None:
            if block == "broke":
                sound.play(SFX_SHIELD_LOSS)
            spawn_food(food, snake, world, portals, difficulty, run_stats.score)
            return None
        run_stats.record_death(DEATH_POISON, now_ms)
        return game_state.DEAD

    if eat_kind == "color_wrong":
        sound.play(SFX_EAT)
        if physics.storm_mode == "speed":
            run_stats.record_death(DEATH_STORM, now_ms)
            return game_state.DEAD
        run_stats.add_score(point_delta)
        game_over, shield_broke = shield.on_wrong_color_break()
        if shield_broke:
            sound.play(SFX_SHIELD_LOSS)
        if game_over:
            run_stats.record_death(DEATH_COLOR_FAIL, now_ms)
            return game_state.DEAD
        food.respawn_color_pair(blocked_spawn_cells(snake, world, portals), snake, run_stats.score)
        return None

    if eat_kind in ("normal", "color_correct"):
        sound.play(SFX_EAT)
        snake.queue_growth()
        physics.on_food_eaten()

    if eat_kind == "color_correct":
        shield.on_correct_color()
        sound.play(SFX_SHIELD_GAIN)
        physics.on_food_eaten()

    run_stats.add_score(point_delta)

    if eat_kind == "color_correct":
        food.respawn_color_pair(blocked_spawn_cells(snake, world, portals), snake, run_stats.score)
    else:
        spawn_food(food, snake, world, portals, difficulty, run_stats.score)

    return None

def update_game(
    state: str,
    snake: Snake,
    food: Food,
    run_stats: RunStats,
    world: World,
    physics: PhysicsEngine,
    portals: PortalManager,
    difficulty: DifficultyManager,
    shield: ShieldState,
    sound: SoundManager,
    last_move_ms: int,
    now_ms: int,
) -> tuple[str, int,str, int]:

    storm_warn=""
    storm_warn_until=0
    if state != game_state.PLAYING:
        return state, last_move_ms,"", 0

    portals.update(now_ms, blocked_spawn_cells(snake, world, portals))
    food.update_storm_ball(now_ms, blocked_spawn_cells(snake, world, portals), snake)

    if not physics.allows_movement(run_stats.score):
        return state, last_move_ms,"", 0

    if now_ms - last_move_ms < physics.move_interval_ms(now_ms):
        return state, last_move_ms,"", 0

    move_direction = physics.resolve_direction(snake, world.maze_walls, now_ms, run_stats.score)
    pre_move = snake.snapshot()
    snake.move(move_direction)
    # if world.active_theme == "ice":
    #     sound.play(SFX_MOVE_GLACIER)
    # elif world.active_theme == "storm":
    #     sound.play(SFX_MOVE_CLOUD)

    prev_theme, portal_used = portals.try_teleport(snake, world, world.maze_walls, now_ms)
    if prev_theme is not None:
        if portal_used == "exit":
            sound.play(SFX_TELEPORT_OUT)
            # death- exit-portal after eating poison
            if physics.ate_poison_flag:
                run_stats.record_death(DEATH_STORM, now_ms)
                return game_state.DEAD, now_ms,"", 0
            speed_on = physics.enter_storm_speed(run_stats.score)
            if physics.exit_portal_count >= 2:
                storm_warn = "WARNING: reverse portal speed active!"
                storm_warn_until = now_ms + 2000
        elif portal_used == "entrance":
            sound.play(SFX_TELEPORT)
            physics.on_entry_portal()
        for pos in food.all_positions():
            if pos in world.blocked_cells() or pos in portals.blocked_cells():
                spawn_food(food, snake, world, portals, difficulty, run_stats.score)
                break

    dead_state = process_food_eat(
        food, snake, run_stats, world, physics, portals, difficulty, shield, sound, now_ms
    )
    if dead_state is not None:
        return dead_state, now_ms,"", 0

    death = collides_after_move(snake, world.maze_walls)
    if death is not None:
        if death == DEATH_WALL:
            block = shield.try_block_collision()
            if block is not None:
                hx, hy = snake.head
                snake.body[0] = (hx % GRID_WIDTH, hy % GRID_HEIGHT)
                sound.play(SFX_SHIELD_LOSS)
            else:
                run_stats.record_death(death, now_ms)
                return game_state.DEAD, now_ms,"", 0
        else:
            run_stats.record_death(death, now_ms)
            return game_state.DEAD, now_ms,"", 0

    shield.on_grid_step(head_in_collision_zone(snake, world.maze_walls))

    world.on_grid_step()
    portals.on_grid_step()
    physics.consume_ice_step(run_stats.score)

    return state, now_ms, storm_warn, storm_warn_until


def draw(
    screen: pygame.Surface,
    state: str,
    session: Session,
    run_stats: RunStats,
    snake: Snake,
    food: Food,
    world: World,
    physics: PhysicsEngine,
    portals: PortalManager,

    difficulty: DifficultyManager,
    shield: ShieldState,
    now_ms: int,
    save_data: dict[str, Any],
    new_record: bool,
    menu_selection: int,
    record_popup_until_ms: int,
    storm_warning_msg: str,
    storm_warning_until_ms: int,
    assets: dict,
) -> None:

    if state == game_state.PRECAUTIONS:
        draw_precautions(screen, assets)
        return
    high_score = get_high_score(save_data)

    if state == game_state.MENU:
        draw_main_menu(screen, menu_selection, high_score, assets)
        return

    draw_playfield(screen, snake, food, world, portals, GRID_WIDTH, GRID_HEIGHT, shield, now_ms, assets)
    draw_hud(screen, run_stats, now_ms, world, assets)
    draw_wrong_color_warning(screen, shield.consecutive_breaks_without_correct, assets)
    if state == game_state.PLAYING and now_ms < storm_warning_until_ms:
        draw_storm_warning(screen, storm_warning_msg, now_ms, assets)
    draw_color_target(screen, food, assets)
    if state == game_state.PLAYING and now_ms < record_popup_until_ms:
        draw_new_record_popup(screen, run_stats.score, now_ms, assets)


    if state == game_state.PAUSED:
        draw_pause_overlay(screen, assets)
    elif state == game_state.DEAD:
        draw_game_over(screen, session, run_stats, now_ms, high_score, new_record, world, save_data, assets)


def load_assets() -> dict:
    """Load all images, fonts, and sounds once at startup."""
    import os
    ASSETS = "assets"

    def img(name: str, size: tuple[int, int] | None = None) -> pygame.Surface:
        path = os.path.join(ASSETS, name)
        surf = pygame.image.load(path).convert_alpha()
        if size:
            surf = pygame.transform.scale(surf, size)
        return surf

    cell = (CELL_SIZE, CELL_SIZE)
    item_snake = (CELL_SIZE+10, CELL_SIZE+10)
    item = (CELL_SIZE+20, CELL_SIZE+20)
    playfield = (WINDOW_WIDTH, WINDOW_HEIGHT - HUD_HEIGHT)

    return {
        "snake_head":       img("snake_head.png",       item_snake),
        "snake_body":       img("snake_body.png",       item_snake),
        "snake_tail":       img("snake_tail.png",       item_snake),
        "snake_head_dead":  img("snake_head_dead_poison_eat.png", item_snake),
        "shield_head":      img("shield_head.png",      item_snake),
        "shield_body":      img("shield_body.png",      item_snake),
        "tail_shield":      img("tail_shield.png",      item_snake),
        "food_green":       img("food_green.png",       item),
        "food_red":         img("food_red.png",         item),
        "food_violet":      img("food_violet.png",      item),
        "poison":           img("poison.png",           item),
        "entry_portal":     img("entry_portal.png",     item),
        "exit_portal":      img("exit_portal.png",      item),

        "bg_forest":  img("forest.png",  playfield),
        "bg_desert":  img("desert.png",  playfield),
        "bg_ice":     img("ice.png",     playfield),
        "bg_storm":   img("storm.png",   playfield),
        "bg_maze":    img("maze.png",    playfield),

        "start_page":        img("start_page.png",        (800, 600)),
        "finish_game":       img("finish_game.png",       (800, 600)),
        "high_score_finish": img("high_score_finish.png", (800, 600)),

        "font_menu_title": pygame.font.Font(os.path.join(ASSETS, "Menu_page_precaution.ttf"), 72),
        "font_menu_item":  pygame.font.Font(os.path.join(ASSETS, "Menu_page_precaution.ttf"), 36),
        "font_menu_hint":  pygame.font.Font(os.path.join(ASSETS, "Menu_page_precaution.ttf"), 20),
        "font_hud":        pygame.font.Font(os.path.join(ASSETS, "inGame.ttf"), 18),
        "font_body":       pygame.font.Font(os.path.join(ASSETS, "inGame.ttf"), 22),
        "font_big":        pygame.font.Font(os.path.join(ASSETS, "inGame.ttf"), 44),

        "stroop_violet": img("food_violet.png", item),
        "stroop_green":  img("food_green.png",  item),
        "stroop_red":    img("food_red.png",    item),
        "stroop_violet": img("food_violet.png", item),
        "stroop_yellow":  img("food_yellow.png",  item),
        "stroop_pink":    img("food_pink.png",    item),
    }

def main() -> None:
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    assets = load_assets()

    save_data = load_save()
    difficulty = DifficultyManager()
    sound = SoundManager()
    shield = ShieldState()
    session = Session()
    run_stats = RunStats()

    snake = Snake()
    food = Food()
    world = World()
    physics = PhysicsEngine(world, difficulty)
    portals = PortalManager()

    now_ms = pygame.time.get_ticks()

    state = game_state.MENU
    sound.play_menu_music()
    menu_selection = 0
    show_precautions = False
    storm_warning_msg = ""
    storm_warning_until_ms = 0
    last_move_ms = now_ms
    new_record = False
    death_saved = False
    baseline_high_score = get_high_score(save_data)
    record_popup_until_ms = 0
    record_popup_shown = False

    running = True
    while running:
        now_ms = pygame.time.get_ticks()
        running, state, move_reset, menu_selection = handle_events(
            state, snake, food, run_stats, world, physics, portals, difficulty, shield, sound, menu_selection, save_data, session, now_ms
        )
        if move_reset is not None:
            last_move_ms = move_reset
            death_saved = False
            new_record = False
            baseline_high_score = get_high_score(save_data)
            record_popup_until_ms = 0
            record_popup_shown = False

        prev_state = state
        state, last_move_ms, sw_msg, sw_until = update_game(
            state, snake, food, run_stats, world, physics, portals, difficulty, shield, sound, last_move_ms, now_ms
        )
        if sw_msg:
            storm_warning_msg = sw_msg
            storm_warning_until_ms = sw_until

        if (
            state == game_state.PLAYING
            and not record_popup_shown
            and run_stats.score > baseline_high_score
        ):
            record_popup_shown = True
            record_popup_until_ms = now_ms + 1000
            sound.play(SFX_RECORD)

        if state == game_state.DEAD and prev_state != game_state.DEAD:
            sound.play(SFX_DIE)
            sound.play_game_over_music()
            if not death_saved:
                new_record = record_run(save_data, session, run_stats, now_ms)
                if record_popup_shown:
                    new_record = False
                session.note_score(run_stats.score)
                death_saved = True

        draw(
            screen, state, session, run_stats, snake, food, world, physics, portals,
             difficulty, shield, now_ms, save_data, new_record, menu_selection,
            record_popup_until_ms, storm_warning_msg, storm_warning_until_ms, assets,
        )
        pygame.display.flip()
        clock.tick(TARGET_FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
