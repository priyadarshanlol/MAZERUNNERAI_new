"""levels.py - the ONE source of truth for every maze.

Legend:  #  wall      .  floor      P  player start
         M  enemy start            E  exit
Every layout is 15 x 15 and is checked by test_levels.py
(solvable, enemy can reach the player, markers present).
"""

LEVELS = [
    {
        "name": "THE WARM-UP",
        "theme": {"wall_top": (28, 40, 90), "wall_side": (10, 14, 40),
                  "wall_panel": (38, 56, 120), "accent": (0, 220, 255)},
        "layout": [
            "###############",
            "#P....#.......#",
            "#.###.#.#####.#",
            "#.#...#.#...#.#",
            "#.#.###.#.#.#.#",
            "#.#.....#.#...#",
            "#.#######.#####",
            "#........M#...#",
            "#.#######.#.#.#",
            "#.#.....#...#.#",
            "#.#.###.#####.#",
            "#...#.#.......#",
            "#.###.#.#####.#",
            "#.....#.#....E#",
            "###############",
        ],
    },
    {
        "name": "NEON MAZE",
        "theme": {"wall_top": (70, 24, 90), "wall_side": (28, 8, 40),
                  "wall_panel": (104, 36, 130), "accent": (255, 60, 220)},
        "layout": [
            "###############",
            "#P............#",
            "#.###.#.#####.#",
            "#...#...#.....#",
            "#.#.###.#.#####",
            "#.#.#.....#...#",
            "#.#.#.###.#.#.#",
            "#.#.#...#.#...#",
            "#.#.###.#.###.#",
            "#...#...#.....#",
            "#.###M#######.#",
            "#...#.#.......#",
            "###.#.#.#######",
            "#.....#......E#",
            "###############",
        ],
    },
    {
        "name": "THE LABYRINTH",
        "theme": {"wall_top": (90, 40, 24), "wall_side": (40, 14, 8),
                  "wall_panel": (130, 60, 30), "accent": (255, 170, 40)},
        "layout": [
            "###############",
            "#P#...........#",
            "#.#######.#.#.#",
            "#.......#.#..E#",
            "#####.#.#.#####",
            "#.....#.#.#...#",
            "#.#####.#.#.#.#",
            "#....M..#...#.#",
            "#.#######.###.#",
            "#.......#...#.#",
            "#####.#.#####.#",
            "#...#.......#.#",
            "#.#.#.#.#.#.#.#",
            "#.#...........#",
            "###############",
        ],
    },
]


def load_level(index):
    """Turn level number `index` into a dict the game can use.

    Returns: name, theme, grid (2D list of 0/1), player_start, enemy_start, exit
    Raises IndexError for a level that does not exist.
    """
    if not 0 <= index < len(LEVELS):
        raise IndexError("There is no level number %d" % index)

    data = LEVELS[index]
    grid = []
    markers = {}
    for row, line in enumerate(data["layout"]):
        grid_row = []
        for col, char in enumerate(line):
            grid_row.append(1 if char == "#" else 0)
            if char in "PME":
                markers[char] = (row, col)
        grid.append(grid_row)

    return {
        "name": data["name"],
        "theme": data["theme"],
        "grid": grid,
        "player_start": markers["P"],
        "enemy_start": markers["M"],
        "exit": markers["E"],
    }
