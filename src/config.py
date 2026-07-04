"""Tweakable gameplay settings."""

# Milliseconds between each grid step the snake takes (~60-90s average run)
MOVE_INTERVAL_MS = 135

# Points awarded per food eaten (used in later phases)
POINTS_PER_FOOD = 10

# Theme lifecycle: auto-shift after this many points without using a portal
THEME_SHIFT_POINTS = 30

# Desert: move interval multiplier when no arrow key is held
DESERT_SLOW_MULTIPLIER = 2

# Ice: grid steps granted per arrow key press (no movement without a press)
ICE_PRESS_STEPS = 3

# Storm: grid steps without wind after entering the storm theme
STORM_GRACE_STEPS = 8

# Storm: wind deflections per storm visit (random in this inclusive range)
STORM_GUST_MIN = 1
STORM_GUST_MAX = 2

# Black storm ball: speed multiplier and duration (milliseconds)
SPEED_BOOST_MULTIPLIER = 3
SPEED_BOOST_MS = 6000

# Black storm ball visibility cycle (milliseconds)
STORM_BALL_VISIBLE_MIN_MS = 6_000
STORM_BALL_VISIBLE_MAX_MS = 10_000
STORM_BALL_HIDDEN_MIN_MS = 8_000
STORM_BALL_HIDDEN_MAX_MS = 14_000

# Portal: movement-step cooldown after a teleport
PORTAL_COOLDOWN_STEPS = 15

# Portal: clearance radius (cells) required around each portal
PORTAL_CLEARANCE = 2

# Portal: visible / hidden phase durations (milliseconds)
PORTAL_VISIBLE_MIN_MS = 10_000
PORTAL_VISIBLE_MAX_MS = 18_000
PORTAL_HIDDEN_MIN_MS = 5_000
PORTAL_HIDDEN_MAX_MS = 10_000

# Points lost for wrong color pick (Phase 8; expanded in Phase 9)
POINTS_COLOR_WRONG = 5

# Chance a poison tile spawns each respawn at 151+ points
POISON_SPAWN_CHANCE = 0.28

# Shield mechanics (Phase 9)
INVULNERABILITY_TICKS = 10
OUTSIDE_COLLISION_STEPS_REQUIRED = 5
SHIELD_BREAK_GAME_OVER_LIMIT = 3
