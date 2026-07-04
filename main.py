"""Advanced Snake — entry point and main game loop."""

import random
import sys
from typing import Any

import pygame

from src import game_state
from src.config import STORM_BALL_HIDDEN_MAX_MS, STORM_BALL_HIDDEN_MIN_MS
from src.constants import GRID_HEIGHT, GRID_WIDTH, TARGET_FPS, WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH
from src.debug_overlay import DebugOverlay
from src.difficulty import DifficultyManager
from src.food import Food
from src.live_settings import LiveSettings
from src.physics import PhysicsEngine, collides_after_move, head_in_collision_zone
from src.portals import PortalManager
from src.save_manager import get_high_score, load_save, record_run, reset_all_save
from src.scoring import DEATH_COLOR_FAIL, DEATH_POISON, DEATH_SELF, DEATH_WALL, RunStats, Session
from src.shield import ShieldState
from src.snake import Snake
from src.sound_manager import (
    SFX_DIE,
    SFX_EAT,
    SFX_POISON,
    SFX_RECORD,
    SFX_SHIELD_GAIN,
    SFX_SHIELD_LOSS,
    SFX_TELEPORT,
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
    draw_storm_grace_hint,
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


def on_storm_theme_entered(world: World, physics: PhysicsEngine) -> None:
    physics.on_storm_entered()


def handle_theme_change(prev_theme: str | None, world: World, physics: PhysicsEngine) -> None:
    if world.active_theme == STORM and prev_theme != STORM:
        on_storm_theme_entered(world, physics)


def handle_events(
    state: str,
    snake: Snake,
    food: Food,
    run_stats: RunStats,
    world: World,
    physics: PhysicsEngine,
    portals: PortalManager,
    debug: DebugOverlay,
    live: LiveSettings,
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
                elif event.key == pygame.K_DOWN:
                    menu_selection = (menu_selection + 1) % len(MENU_ITEMS)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if menu_selection == 0:
                        move_reset = reset_run(
                            snake, food, run_stats, world, physics, portals, difficulty, shield, now_ms
                        )
                        new_state = game_state.PLAYING
                    elif menu_selection == 1:
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

            if event.key == pygame.K_F1:
                debug.toggle()
                continue

            if new_state == game_state.DEAD and event.key == pygame.K_h:
                new_state = game_state.MENU
                continue

            if debug.handle_key(event.key, live, world, physics, difficulty):
                if event.key == pygame.K_t:
                    spawn_food(food, snake, world, portals, difficulty, run_stats.score)
                continue

            key_name = ARROW_KEY_MAP.get(event.key)

            if new_state == game_state.PAUSED:
                if event.key in (pygame.K_p, pygame.K_ESCAPE):
                    new_state = game_state.PLAYING
                continue

            if event.key == pygame.K_ESCAPE:
                return False, new_state, move_reset, menu_selection

            if new_state == game_state.PLAYING:
                if event.key == pygame.K_p:
                    new_state = game_state.PAUSED
                elif event.key == pygame.K_F2:
                    prev_theme = world.active_theme
                    world.enter_storm(now_ms)
                    handle_theme_change(prev_theme, world, physics)
                elif key_name is not None:
                    physics.on_key_down(key_name, run_stats.score)
                    snake.set_direction_from_key(key_name)

            if new_state == game_state.DEAD and event.key == pygame.K_r:
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
        physics.activate_speed_boost(now_ms)
        prev_theme = world.active_theme
        world.enter_storm(now_ms)
        handle_theme_change(prev_theme, world, physics)
        return None

    if eat_kind == "poison":
        sound.play(SFX_POISON)
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

    if eat_kind == "color_correct":
        shield.on_correct_color()
        sound.play(SFX_SHIELD_GAIN)

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
) -> tuple[str, int]:
    if state != game_state.PLAYING:
        return state, last_move_ms

    portals.update(now_ms, blocked_spawn_cells(snake, world, portals))
    food.update_storm_ball(now_ms, blocked_spawn_cells(snake, world, portals), snake)

    if not physics.allows_movement(run_stats.score):
        return state, last_move_ms

    if now_ms - last_move_ms < physics.move_interval_ms(now_ms):
        return state, last_move_ms

    move_direction = physics.resolve_direction(snake, world.maze_walls, now_ms, run_stats.score)
    pre_move = snake.snapshot()
    snake.move(move_direction)

    prev_theme, _portal_used = portals.try_teleport(snake, world, world.maze_walls, now_ms)
    if prev_theme is not None:
        sound.play(SFX_TELEPORT)
        handle_theme_change(prev_theme, world, physics)
        for pos in food.all_positions():
            if pos in world.blocked_cells() or pos in portals.blocked_cells():
                spawn_food(food, snake, world, portals, difficulty, run_stats.score)
                break

    dead_state = process_food_eat(
        food, snake, run_stats, world, physics, portals, difficulty, shield, sound, now_ms
    )
    if dead_state is not None:
        return dead_state, now_ms

    death = collides_after_move(snake, world.maze_walls)
    if death is not None:
        if shield.is_invulnerable():
            if death == DEATH_WALL:
                snake.restore(pre_move)
            else:
                run_stats.record_death(death, now_ms)
                return game_state.DEAD, now_ms
        else:
            block = shield.try_block_collision()
            if block in ("broke", "invuln"):
                snake.restore(pre_move)
                if block == "broke":
                    sound.play(SFX_SHIELD_LOSS)
            else:
                run_stats.record_death(death, now_ms)
                return game_state.DEAD, now_ms

    shield.on_grid_step(head_in_collision_zone(snake, world.maze_walls))

    world.on_grid_step()
    portals.on_grid_step()
    physics.consume_ice_step(run_stats.score)

    return state, now_ms


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
    debug: DebugOverlay,
    live: LiveSettings,
    difficulty: DifficultyManager,
    shield: ShieldState,
    now_ms: int,
    save_data: dict[str, Any],
    new_record: bool,
    menu_selection: int,
    record_popup_until_ms: int,
) -> None:
    high_score = get_high_score(save_data)

    if state == game_state.MENU:
        draw_main_menu(screen, menu_selection, high_score)
        return

    draw_playfield(screen, snake, food, world, portals, GRID_WIDTH, GRID_HEIGHT, shield, now_ms)
    draw_hud(screen, run_stats, now_ms, world)
    draw_color_target(screen, food)
    if state == game_state.PLAYING and now_ms < record_popup_until_ms:
        draw_new_record_popup(screen, run_stats.score, now_ms)
    draw_storm_grace_hint(screen, world, physics, now_ms)
    debug.draw(screen, snake, world, physics, portals, live, difficulty, run_stats.score, now_ms)

    if state == game_state.PAUSED:
        draw_pause_overlay(screen)
    elif state == game_state.DEAD:
        draw_game_over(screen, session, run_stats, now_ms, high_score, new_record, world, save_data)


def main() -> None:
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    save_data = load_save()
    live = LiveSettings()
    debug = DebugOverlay()
    difficulty = DifficultyManager()
    sound = SoundManager()
    shield = ShieldState()
    session = Session()
    run_stats = RunStats()
    world = World(live)
    physics = PhysicsEngine(world, live, difficulty)
    portals = PortalManager(live)
    snake = Snake()
    food = Food()

    now_ms = pygame.time.get_ticks()

    state = game_state.MENU
    menu_selection = 0
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
            state, snake, food, run_stats, world, physics, portals, debug, live, difficulty, shield, sound, menu_selection, save_data, session, now_ms
        )
        if move_reset is not None:
            last_move_ms = move_reset
            death_saved = False
            new_record = False
            baseline_high_score = get_high_score(save_data)
            record_popup_until_ms = 0
            record_popup_shown = False

        prev_state = state
        state, last_move_ms = update_game(
            state, snake, food, run_stats, world, physics, portals, difficulty, shield, sound, last_move_ms, now_ms
        )

        if (
            state == game_state.PLAYING
            and not record_popup_shown
            and run_stats.score > baseline_high_score
        ):
            record_popup_shown = True
            record_popup_until_ms = now_ms + 2500
            sound.play(SFX_RECORD)

        if state == game_state.DEAD and prev_state != game_state.DEAD:
            sound.play(SFX_DIE)
            if not death_saved:
                new_record = record_run(save_data, session, run_stats, now_ms)
                session.note_score(run_stats.score)
                death_saved = True

        draw(
            screen, state, session, run_stats, snake, food, world, physics, portals,
            debug, live, difficulty, shield, now_ms, save_data, new_record, menu_selection, record_popup_until_ms,
        )
        pygame.display.flip()
        clock.tick(TARGET_FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
