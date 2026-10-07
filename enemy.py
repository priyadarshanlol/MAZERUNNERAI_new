"""enemy.py - the Cyber-Bot that hunts the player using BFS."""
import math
import pygame
from settings import *
from particles import draw_glow
from pathfinding import find_path
from player import get_shadow

_overlay = None     # transparent layer for the BFS visualiser (made once)


def draw_bot(canvas, x, y, t, rage=0.0, scale=1.0):
    """Draw the hovering robot centred on pixel (x, y)."""
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    shadow = get_shadow(30 * scale, 10 * scale)
    canvas.blit(shadow, shadow.get_rect(center=(x, y + 14 * scale)))
    cy = y - 5 * scale + math.sin(t * 3.2) * 3 * scale

    draw_glow(canvas, (x, cy), 72 * scale, (255, 40, 70), 0.45 + 0.25 * pulse + 0.25 * rage)

    # rotating radar wedge with a fading tail
    r = int(58 * scale)
    wedge = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    angle = t * 3.5
    for i in range(5, -1, -1):
        a0 = angle - i * 0.18
        pts = [(r, r)] + [(r + math.cos(a0 + k * 0.1) * r, r + math.sin(a0 + k * 0.1) * r) for k in range(4)]
        pygame.draw.polygon(wedge, (255, 60, 90, 78 - i * 12), pts)
    canvas.blit(wedge, (x - r, cy - r))

    draw_glow(canvas, (x, cy + 13 * scale), 16 * scale, (255, 170, 40), 0.6 + 0.4 * pulse)
    body = pygame.Rect(0, 0, int(30 * scale), int(24 * scale))
    body.center = (x, cy)
    pygame.draw.rect(canvas, (52, 22, 64), body, border_radius=8)
    pygame.draw.rect(canvas, (255, 60, 90), body, 2, border_radius=8)
    visor = pygame.Rect(0, 0, int(22 * scale), int(9 * scale))
    visor.center = (x, cy - 2 * scale)
    pygame.draw.rect(canvas, (20, 0, 12), visor, border_radius=4)
    scan = x + math.sin(t * 4) * 8 * scale          # the scanning red eye
    pygame.draw.rect(canvas, (255, 70, 70), (scan - 3 * scale, visor.y + 1, 6 * scale, visor.h - 2), border_radius=2)
    pygame.draw.line(canvas, (200, 200, 225), (x, body.top), (x, body.top - 8 * scale), 2)
    bulb = (255, 255, 120) if (t * 4) % 1 < 0.5 else (120, 40, 40)
    pygame.draw.circle(canvas, bulb, (int(x), int(body.top - 9 * scale)), max(2, int(3 * scale)))
    for side in (-1, 1):
        pygame.draw.circle(canvas, (255, 90, 110), (int(x + side * 11 * scale), int(cy + 6 * scale)), max(1, int(2 * scale)))


class Enemy:
    def __init__(self, cell, step_ms, recalc_ms):
        self.cell = cell               # logical cell (row, col)
        self.prev = cell
        self.step_ms = step_ms
        self.recalc_ms = recalc_ms
        self.since_step = float(step_ms)
        self.step_timer = 0.0          # ms until the next step
        self.recalc_timer = 0.0        # ms until BFS runs again
        self.path = []                 # path[0] is always self.cell
        self.explored = []             # cells BFS looked at (for the flood effect)
        self.wave_time = 9999.0

    # ---- AI ----
    def recalculate(self, maze, target):
        """Run BFS from the enemy's cell to the player's cell."""
        self.explored = []
        self.path = find_path(maze.grid, self.cell, target, self.explored)
        self.wave_time = 0.0
        self.recalc_timer = self.recalc_ms

    def update(self, dt_ms, maze, target):
        self.since_step += dt_ms
        self.wave_time += dt_ms
        self.recalc_timer -= dt_ms
        if self.recalc_timer <= 0 or not self.path:
            self.recalculate(maze, target)

        self.step_timer -= dt_ms
        if self.step_timer <= 0:
            if len(self.path) > 1 and maze.is_walkable(self.path[1]):
                overshoot = -self.step_timer
                self.step_timer += self.step_ms
                self.prev, self.cell = self.cell, self.path[1]
                self.path.pop(0)                  # keep path[0] == self.cell
                self.since_step = overshoot
            else:
                self.step_timer = 0.0             # no path: wait and re-check

    # ---- positions ----
    def visual(self):
        p = min(1.0, self.since_step / self.step_ms)
        return (self.prev[0] + (self.cell[0] - self.prev[0]) * p,
                self.prev[1] + (self.cell[1] - self.prev[1]) * p)

    def pixel(self):
        row, col = self.visual()
        return MAZE_X + (col + 0.5) * TILE, MAZE_Y + (row + 0.5) * TILE

    # ---- drawing ----
    def draw(self, canvas, t, rage=0.0):
        x, y = self.pixel()
        draw_bot(canvas, x, y, t, rage)

    def draw_path(self, canvas, t):
        """BFS visualiser: flood wave, highlighted route, flowing energy dots."""
        global _overlay
        if _overlay is None:
            _overlay = pygame.Surface((MAZE_PX, MAZE_PX), pygame.SRCALPHA)
        _overlay.fill((0, 0, 0, 0))

        count = len(self.explored)
        if count and self.wave_time < 900:
            per_cell = 260 / count
            for i, (row, col) in enumerate(self.explored):
                age = self.wave_time - i * per_cell
                alpha = int(60 * (1 - age / 600)) if age >= 0 else 0
                if alpha > 3:
                    pygame.draw.rect(_overlay, (0, 230, 255, alpha),
                                     (col * TILE + 3, row * TILE + 3, TILE - 6, TILE - 6), border_radius=6)

        for row, col in self.path:
            pygame.draw.rect(_overlay, (255, 215, 60, 55),
                             (col * TILE + 6, row * TILE + 6, TILE - 12, TILE - 12), border_radius=5)

        ex, ey = self.pixel()
        points = [(ex, ey)] + [(MAZE_X + (c + 0.5) * TILE, MAZE_Y + (r + 0.5) * TILE) for r, c in self.path]
        local = [(px - MAZE_X, py - MAZE_Y) for px, py in points]
        if len(local) > 1:
            pygame.draw.lines(_overlay, (255, 215, 60, 70), False, local, 9)
            pygame.draw.lines(_overlay, (255, 230, 120, 190), False, local, 2)
        canvas.blit(_overlay, (MAZE_X, MAZE_Y))

        if len(points) > 1:                       # energy dots flowing enemy -> player
            lengths = [math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)]
            total = sum(lengths)
            gap = 46
            for k in range(int(total // gap) + 1):
                s = (t * 160 + k * gap) % max(total, 1)
                for i, seg in enumerate(lengths):
                    if s <= seg:
                        f = s / seg if seg else 0
                        dx = points[i][0] + (points[i + 1][0] - points[i][0]) * f
                        dy = points[i][1] + (points[i + 1][1] - points[i][1]) * f
                        draw_glow(canvas, (dx, dy), 10, (255, 230, 120), 0.9)
                        pygame.draw.circle(canvas, (255, 255, 255), (int(dx), int(dy)), 2)
                        break
                    s -= seg
