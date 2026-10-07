"""maze.py - the grid, plus drawing of walls, floor and the exit portal."""
import math
import pygame
from settings import *
from particles import draw_glow

FLOOR_A = (12, 14, 34)
FLOOR_B = (16, 18, 42)
FLOOR_LINE = (24, 28, 60)
WALL_DEPTH = 10      # height of the "front face" that fakes a 2.5D look


class Maze:
    """grid[row][col]: 1 = wall, 0 = floor."""

    def __init__(self, level):
        self.grid = level["grid"]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.player_start = level["player_start"]
        self.enemy_start = level["enemy_start"]
        self.exit = level["exit"]
        self.theme = level["theme"]
        self.name = level["name"]
        self.base = self._build_base()      # walls + floor, drawn once
        self.glow = self._build_glow()      # soft neon halo around the walls

    # ---- grid queries ----
    def is_walkable(self, cell):
        """True only for a floor cell that is inside the maze."""
        row, col = cell
        return 0 <= row < self.rows and 0 <= col < self.cols and self.grid[row][col] == 0

    def _is_floor(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols and self.grid[row][col] == 0

    @staticmethod
    def cell_to_pixel(row, col):
        """Centre of a cell on screen (row/col may be fractions while moving)."""
        return MAZE_X + (col + 0.5) * TILE, MAZE_Y + (row + 0.5) * TILE

    # ---- pre-rendering ----
    def _build_base(self):
        surf = pygame.Surface((MAZE_PX, MAZE_PX))
        theme = self.theme
        accent = theme["accent"]
        shade = pygame.Surface((TILE, 12), pygame.SRCALPHA)
        for y in range(12):
            pygame.draw.line(shade, (0, 0, 0, int(120 * (1 - y / 12))), (0, y), (TILE, y))

        for row in range(self.rows):
            for col in range(self.cols):
                x, y = col * TILE, row * TILE
                if self.grid[row][col] == 0:
                    pygame.draw.rect(surf, FLOOR_A if (row + col) % 2 == 0 else FLOOR_B, (x, y, TILE, TILE))
                    pygame.draw.rect(surf, FLOOR_LINE, (x, y, TILE, TILE), 1)
                    if not self._is_floor(row - 1, col):
                        surf.blit(shade, (x, y))        # shadow under a wall

        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] != 1:
                    continue
                x, y = col * TILE, row * TILE
                below_open = self._is_floor(row + 1, col)
                top_h = TILE - WALL_DEPTH if below_open else TILE
                pygame.draw.rect(surf, theme["wall_side"], (x, y, TILE, TILE))
                pygame.draw.rect(surf, theme["wall_top"], (x, y, TILE, top_h))
                if top_h > 12:
                    pygame.draw.rect(surf, theme["wall_panel"], (x + 5, y + 5, TILE - 10, top_h - 10), border_radius=4)
                    pygame.draw.circle(surf, theme["wall_top"], (x + TILE // 2, y + top_h // 2), 3)
                if self._is_floor(row - 1, col):
                    pygame.draw.line(surf, accent, (x, y), (x + TILE - 1, y), 2)
                if self._is_floor(row, col - 1):
                    pygame.draw.line(surf, accent, (x, y), (x, y + top_h), 2)
                if self._is_floor(row, col + 1):
                    pygame.draw.line(surf, accent, (x + TILE - 2, y), (x + TILE - 2, y + top_h), 2)
                if below_open:
                    dark = tuple(c // 2 for c in accent)
                    pygame.draw.line(surf, dark, (x, y + top_h), (x + TILE - 1, y + top_h), 2)
        return surf

    def _build_glow(self):
        big = pygame.Surface((MAZE_PX, MAZE_PX), pygame.SRCALPHA)
        accent = self.theme["accent"]
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] != 1:
                    continue
                x, y = col * TILE, row * TILE
                for d_row, d_col, a, b in ((-1, 0, (x, y), (x + TILE, y)),
                                           (1, 0, (x, y + TILE), (x + TILE, y + TILE)),
                                           (0, -1, (x, y), (x, y + TILE)),
                                           (0, 1, (x + TILE, y), (x + TILE, y + TILE))):
                    if self._is_floor(row + d_row, col + d_col):
                        pygame.draw.line(big, (*accent, 255), a, b, 10)
        small = pygame.transform.smoothscale(big, (MAZE_PX // 5, MAZE_PX // 5))
        return pygame.transform.smoothscale(small, (MAZE_PX, MAZE_PX))

    # ---- drawing ----
    def draw_base(self, canvas, t):
        canvas.blit(self.base, (MAZE_X, MAZE_Y))
        self.glow.set_alpha(int(170 + 70 * math.sin(t * 2)))
        canvas.blit(self.glow, (MAZE_X, MAZE_Y))

    def draw_exit(self, canvas, t, scale=1.0):
        """Animated swirling portal."""
        cx, cy = self.cell_to_pixel(*self.exit)
        pulse = 0.75 + 0.25 * math.sin(t * 4)
        draw_glow(canvas, (cx, cy), 80 * scale, (0, 255, 150), 0.7 * pulse)
        draw_glow(canvas, (cx, cy), 36 * scale, (200, 255, 255), 0.5)
        for i in range(3):
            radius = (TILE * 0.46 - i * 6) * scale
            if radius < 3:
                continue
            spin = t * (2.5 + i) * (1 if i % 2 == 0 else -1)
            rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
            color = (80 + i * 60, 255, 200 - i * 40)
            pygame.draw.arc(canvas, color, rect, spin, spin + 2.4, 3)
            pygame.draw.arc(canvas, color, rect, spin + 3.14, spin + 5.4, 3)
        for i in range(6):                       # spiral of dots falling inwards
            k = (t * 0.8 + i / 6) % 1
            a = t * 3 + i * 1.047
            r = (1 - k) * TILE * 0.5 * scale
            pygame.draw.circle(canvas, (200, 255, 230), (int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)), 2)
        pygame.draw.circle(canvas, (255, 255, 255), (int(cx), int(cy)), max(1, int((4 + pulse * 2) * scale)))
