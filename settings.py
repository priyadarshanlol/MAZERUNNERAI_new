"""settings.py - every tunable number and colour lives here."""

# ---- window ---------------------------------------------------------------
WIDTH, HEIGHT = 960, 720
FPS = 60

# ---- grid -----------------------------------------------------------------
GRID_SIZE = 15                       # 15 x 15 cells
TILE = 40                            # pixels per cell
MAZE_PX = GRID_SIZE * TILE           # 600
MAZE_X = (WIDTH - MAZE_PX) // 2      # where the maze starts on screen
MAZE_Y = 100

# ---- gameplay -------------------------------------------------------------
PLAYER_STEP_MS = 115                 # player takes one cell every 115 ms
READY_SECONDS = 3.0                  # 3-2-1 countdown before each level
CATCH_DISTANCE = 0.55                # enemy closer than this (in cells) = caught
SHOW_BFS_PATH = True                 # start with the BFS visualiser ON (V toggles)

# enemy_step_ms : time the enemy needs for ONE cell (bigger = slower)
# recalc_ms     : how often the enemy re-runs BFS
# time_limit    : seconds on the countdown clock
DIFFICULTIES = {
    "EASY":   {"enemy_step_ms": 330, "recalc_ms": 450, "time_limit": 60,
               "color": (80, 255, 160),  "blurb": "Slow enemy  -  60 seconds"},
    "MEDIUM": {"enemy_step_ms": 240, "recalc_ms": 300, "time_limit": 45,
               "color": (255, 210, 70),  "blurb": "Normal enemy  -  45 seconds"},
    "HARD":   {"enemy_step_ms": 170, "recalc_ms": 200, "time_limit": 30,
               "color": (255, 70, 90),   "blurb": "Fast enemy  -  30 seconds"},
}
DIFFICULTY_NAMES = ["EASY", "MEDIUM", "HARD"]

# ---- colours --------------------------------------------------------------
WHITE = (240, 245, 255)
DIM = (120, 130, 170)
CYAN = (0, 240, 255)
MAGENTA = (255, 40, 200)
YELLOW = (255, 220, 70)
GREEN = (80, 255, 160)
RED = (255, 60, 90)
