"""player.py - the glowing blob hero."""
import math
import pygame
from settings import *
from particles import draw_glow

_shadows = {}


def get_shadow(w, h):
    """Soft dark ellipse that sits under characters (cached)."""
    key = (int(w), int(h))
    if key not in _shadows:
        surf = pygame.Surface(key, pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 120), surf.get_rect())
        _shadows[key] = surf
    return _shadows[key]


def draw_blob(canvas, x, y, t, facing=(0, 1), stretch=0.0, scale=1.0, hop=0.0):
    """Draw the hero centred on pixel (x, y).

    facing  : (d_row, d_col) direction the eyes look
    stretch : >0 stretches along the move direction, <0 squashes (landing)
    hop     : pixels the blob is lifted off the floor
    """
    radius = TILE * 0.38 * scale
    shadow = get_shadow(34 * scale * (1 - hop / 40), 12 * scale)
    canvas.blit(shadow, shadow.get_rect(center=(x, y + 13 * scale)))
    y -= hop
    draw_glow(canvas, (x, y), 54 * scale, CYAN, 0.55)

    breathe = 0.04 * math.sin(t * 5)
    vertical = facing[0] != 0
    sx = 1 + (-0.18 * stretch if vertical else 0.25 * stretch) - breathe
    sy = 1 + (0.25 * stretch if vertical else -0.18 * stretch) + breathe
    body = pygame.Rect(0, 0, int(radius * 2 * sx), int(radius * 2 * sy))
    body.center = (x, y)
    pygame.draw.ellipse(canvas, (0, 110, 160), body)
    pygame.draw.ellipse(canvas, (0, 170, 225), body.inflate(-5, -5))
    mid = body.inflate(-12, -12)
    mid.move_ip(-1, -2)
    pygame.draw.ellipse(canvas, (50, 225, 255), mid)
    pygame.draw.ellipse(canvas, (190, 255, 255),
                        pygame.Rect(body.x + body.w * 0.22, body.y + body.h * 0.14, body.w * 0.28, body.h * 0.18))

    # eyes look where we are going; they blink every few seconds
    blink = (t % 3.3) < 0.12
    eye_dx, eye_dy = facing[1] * 3 * scale, facing[0] * 3 * scale
    for side in (-1, 1):
        ex, ey = x + side * 6 * scale + eye_dx, y - 1 * scale + eye_dy
        if blink:
            pygame.draw.line(canvas, (10, 20, 40), (ex - 4, ey), (ex + 4, ey), 2)
        else:
            pygame.draw.circle(canvas, (255, 255, 255), (int(ex), int(ey)), max(2, int(5 * scale)))
            pygame.draw.circle(canvas, (10, 20, 40),
                               (int(ex + facing[1] * 1.8), int(ey + facing[0] * 1.8)), max(1, int(2.5 * scale)))


class Player:
    """The player lives on a grid cell; the on-screen picture slides smoothly."""

    def __init__(self, cell):
        self.cell = cell               # logical position (row, col)
        self.prev = cell               # where the current slide started
        self.since_step = 999.0        # ms since the last step started
        self.cooldown = 0.0            # ms until the next step is allowed
        self.bump_cooldown = 0.0
        self.facing = (0, 1)
        self.trail = []                # [x, y, life] afterimages

    def visual(self):
        """Smooth (row, col) used for drawing - between prev and cell."""
        p = min(1.0, self.since_step / PLAYER_STEP_MS)
        p = 1 - (1 - p) ** 2           # ease-out
        return (self.prev[0] + (self.cell[0] - self.prev[0]) * p,
                self.prev[1] + (self.cell[1] - self.prev[1]) * p)

    def pixel(self):
        row, col = self.visual()
        return MAZE_X + (col + 0.5) * TILE, MAZE_Y + (row + 0.5) * TILE

    def update(self, dt_ms, wanted, maze):
        """Try to step in direction `wanted` (d_row, d_col) or None.

        Returns "moved", "bumped" (walked into a wall) or None.
        """
        self.since_step += dt_ms
        self.cooldown = max(0.0, self.cooldown - dt_ms)
        self.bump_cooldown = max(0.0, self.bump_cooldown - dt_ms)

        px, py = self.pixel()
        if self.since_step < PLAYER_STEP_MS:
            self.trail.append([px, py, 0.3])
        for item in self.trail:
            item[2] -= dt_ms / 1000
        self.trail = [i for i in self.trail if i[2] > 0]

        if wanted is None or self.cooldown > 0:
            return None
        self.facing = wanted
        target = (self.cell[0] + wanted[0], self.cell[1] + wanted[1])
        if maze.is_walkable(target):          # walls and the outside are blocked here
            self.prev, self.cell = self.cell, target
            self.since_step = 0.0
            self.cooldown = PLAYER_STEP_MS
            return "moved"
        self.cooldown = 90
        if self.bump_cooldown <= 0:
            self.bump_cooldown = 250
            return "bumped"
        return None

    def draw(self, canvas, t, pos=None, scale=1.0):
        for tx, ty, life in self.trail:
            draw_glow(canvas, (tx, ty), 16, CYAN, life / 0.3 * 0.55)
        x, y = pos if pos else self.pixel()
        p = self.since_step / PLAYER_STEP_MS
        if p < 1:
            stretch, hop = math.sin(math.pi * p), math.sin(math.pi * p) * 5
        else:
            k = (self.since_step - PLAYER_STEP_MS) / 100
            stretch, hop = (-0.6 * (1 - k) if k < 1 else 0.0), 0.0
        draw_blob(canvas, x, y, t, self.facing, stretch, scale, hop)
