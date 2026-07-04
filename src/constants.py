"""Fixed values: window size, colors, and target frame rate."""

# Window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_TITLE = "Advanced Snake"

# Grid
CELL_SIZE = 20
HUD_HEIGHT = 24
PLAYFIELD_Y = HUD_HEIGHT
GRID_WIDTH = WINDOW_WIDTH // CELL_SIZE
GRID_HEIGHT = (WINDOW_HEIGHT - HUD_HEIGHT) // CELL_SIZE

# Frame rate
TARGET_FPS = 60

# Colors (RGB)
COLOR_BACKGROUND = (20, 20, 30)
COLOR_GRID_LINE = (35, 35, 50)
COLOR_TEXT = (220, 220, 220)
COLOR_SNAKE_HEAD = (80, 200, 120)
COLOR_SNAKE_BODY = (50, 160, 90)
COLOR_FOOD = (220, 80, 80)
COLOR_FOOD_RED = (220, 60, 60)
COLOR_FOOD_BLUE = (60, 120, 220)
COLOR_POISON = (150, 50, 200)
COLOR_STORM_BALL = (15, 15, 15)
COLOR_GAME_OVER = (255, 100, 100)
COLOR_MAZE_WALL = (90, 90, 110)
COLOR_STORM_WARNING = (255, 200, 80)
COLOR_PORTAL_ENTRANCE = (180, 100, 255)
COLOR_PORTAL_EXIT = (100, 180, 255)
COLOR_PORTAL_COOLDOWN = (100, 100, 120)
COLOR_SHIELD_ITEM = (100, 200, 255)
COLOR_INVULN_FLASH = (255, 255, 180)
COLOR_NEW_RECORD = (255, 215, 0)
COLOR_HUD_PANEL = (12, 12, 22)

# Theme display colors: (background, grid_line)
THEME_PALETTES = {
    "forest": ((18, 42, 28), (28, 62, 38)),
    "desert": ((52, 40, 28), (72, 56, 38)),
    "ice": ((28, 42, 58), (42, 62, 82)),
    "storm": ((32, 32, 48), (48, 48, 68)),
    "maze": ((24, 24, 32), (40, 40, 52)),
}

THEME_LABELS = {
    "forest": "Forest",
    "desert": "Desert",
    "ice": "Ice",
    "storm": "Storm",
    "maze": "Maze",
}
