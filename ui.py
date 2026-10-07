"""ui.py - text, buttons, HUD, animated background, screen effects, 'How AI works'."""
import math
import random
import pygame
from settings import *
from particles import draw_glow
from pathfinding import find_path
from player import draw_blob
from enemy import draw_bot

# ------------------------------------------------------------------ text ----
_fonts = {}
_text_cache = {}
FONT_NAMES = "bahnschrift,segoeui,verdana,dejavusans,arial"


def get_font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont(FONT_NAMES, size, bold=True)
    return _fonts[size]


def render_text(text, size, color, glow=0):
    key = (text, size, color, glow)
    img = _text_cache.get(key)
    if img is None:
        if len(_text_cache) > 700:
            _text_cache.clear()
        base = get_font(size).render(text, True, color)
        if glow:
            img = pygame.Surface((base.get_width() + glow * 4, base.get_height() + glow * 4), pygame.SRCALPHA)
            halo = base.copy()
            halo.set_alpha(20)
            for k in range(12):
                a = k / 12 * 6.283
                for ring in (glow, glow * 0.5):
                    img.blit(halo, (glow * 2 + math.cos(a) * ring, glow * 2 + math.sin(a) * ring))
            img.blit(base, (glow * 2, glow * 2))
        else:
            img = base
        _text_cache[key] = img
    return img


def draw_text(surf, text, size, color, pos, anchor="center", glow=0, scale=1.0, alpha=255):
    img = render_text(text, size, color, glow)
    if scale != 1.0:
        img = pygame.transform.smoothscale(img, (max(1, int(img.get_width() * scale)), max(1, int(img.get_height() * scale))))
    if alpha < 255:
        img = img.copy()
        img.set_alpha(alpha)
    rect = img.get_rect()
    setattr(rect, anchor, pos)
    surf.blit(img, rect)
    return rect


_panel_cache = {}


def draw_panel(surf, rect, fill=(10, 12, 32), alpha=170, border=CYAN, radius=14, border_alpha=200, width=2):
    key = (rect.w, rect.h, fill, alpha, border, radius, border_alpha, width)
    img = _panel_cache.get(key)
    if img is None:
        img = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(img, (*fill, alpha), img.get_rect(), border_radius=radius)
        if width:
            pygame.draw.rect(img, (*border, border_alpha), img.get_rect(), width, border_radius=radius)
        _panel_cache[key] = img
    surf.blit(img, rect.topleft)


def lerp_color(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ------------------------------------------------------------ background ----
class Background:
    """Gradient sky, twinkling stars, drifting colour orbs, scrolling neon floor."""

    def __init__(self):
        self.horizon = int(HEIGHT * 0.6)
        self.sky = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            if y < self.horizon:
                color = lerp_color((4, 4, 18), (34, 8, 60), y / self.horizon)
            else:
                color = lerp_color((16, 4, 34), (4, 2, 14), (y - self.horizon) / (HEIGHT - self.horizon))
            pygame.draw.line(self.sky, color, (0, y), (WIDTH, y))
        rnd = random.Random(7)
        self.stars = [(rnd.randint(0, WIDTH), rnd.randint(0, self.horizon), rnd.uniform(1, 3), rnd.uniform(0, 6.28))
                      for _ in range(110)]
        self.orbs = [[rnd.uniform(0, WIDTH), rnd.uniform(60, 500), rnd.uniform(-14, 14), rnd.uniform(-6, 6),
                      rnd.choice([(90, 20, 160), (0, 90, 150), (150, 20, 90), (30, 60, 160)])] for _ in range(5)]

    def draw(self, surf, t):
        surf.blit(self.sky, (0, 0))
        for orb in self.orbs:
            orb[0] = (orb[0] + orb[2] / 60) % (WIDTH + 400)
            orb[1] += orb[3] / 60
            if not 40 < orb[1] < 520:
                orb[3] = -orb[3]
            draw_glow(surf, (orb[0] - 200, orb[1]), 200, orb[4], 0.6)
        for x, y, speed, phase in self.stars:
            level = int(110 + 140 * (0.5 + 0.5 * math.sin(t * speed + phase)))
            surf.fill((level, level, min(255, level + 30)), (x, y, 2, 2))
        draw_glow(surf, (WIDTH // 2, self.horizon), 260, (140, 20, 160), 0.55)
        # perspective neon floor
        for i in range(-12, 13):
            x2 = WIDTH // 2 + i * 150
            pygame.draw.line(surf, (70, 24, 130), (WIDTH // 2 + i * 14, self.horizon), (x2, HEIGHT), 1)
        for i in range(12):
            z = ((i + t * 0.7) % 12) / 12
            y = self.horizon + (HEIGHT - self.horizon) * z * z
            pygame.draw.line(surf, lerp_color((40, 14, 80), (170, 50, 220), z), (0, y), (WIDTH, y), 1)
        pygame.draw.line(surf, (200, 80, 255), (0, self.horizon), (WIDTH, self.horizon), 2)


class ScreenFX:
    """Dark vignette, red danger vignette and CRT scanlines (built once)."""

    def __init__(self):
        small_w, small_h = 64, 48
        dark = pygame.Surface((small_w, small_h), pygame.SRCALPHA)
        red = pygame.Surface((small_w, small_h), pygame.SRCALPHA)
        for x in range(small_w):
            for y in range(small_h):
                d = math.hypot((x / small_w - 0.5) * 2, (y / small_h - 0.5) * 2)
                k = max(0.0, min(1.0, (d - 0.55) / 0.9))
                dark.set_at((x, y), (0, 0, 8, int(190 * k)))
                red.set_at((x, y), (255, 0, 30, int(255 * k * k)))
        self.dark = pygame.transform.smoothscale(dark, (WIDTH, HEIGHT))
        self.red = pygame.transform.smoothscale(red, (WIDTH, HEIGHT))
        self.scan = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 3):
            pygame.draw.line(self.scan, (0, 0, 0, 34), (0, y), (WIDTH, y))

    def apply(self, canvas, danger, t):
        if danger > 0.02:
            self.red.set_alpha(int(255 * min(1.0, danger) * (0.65 + 0.35 * math.sin(t * 11))))
            canvas.blit(self.red, (0, 0))
        canvas.blit(self.dark, (0, 0))
        canvas.blit(self.scan, (0, 0))


# ---------------------------------------------------------------- menus ----
class Menu:
    """A vertical list of buttons: arrows/W/S + Enter, or the mouse."""

    def __init__(self, options, cx, top, width=340, height=52, gap=14, sound=None):
        self.options = options
        self.selected = 0
        self.sound = sound
        self.rects = [pygame.Rect(cx - width // 2, top + i * (height + gap), width, height)
                      for i in range(len(options))]
        self.anim = [0.0] * len(options)

    def _select(self, index):
        if index != self.selected:
            self.selected = index
            if self.sound:
                self.sound.play("select")

    def handle(self, event):
        """Returns the chosen option text when the player activates a button."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._select((self.selected - 1) % len(self.options))
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._select((self.selected + 1) % len(self.options))
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self.options[self.selected]
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(event.pos):
                    self._select(i)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rects[self.selected].collidepoint(event.pos):
                return self.options[self.selected]
        return None

    def update(self, dt):
        for i in range(len(self.options)):
            goal = 1.0 if i == self.selected else 0.0
            self.anim[i] += (goal - self.anim[i]) * min(1.0, dt * 14)

    def draw(self, surf, t, color=CYAN):
        for i, (name, rect) in enumerate(zip(self.options, self.rects)):
            a = self.anim[i]
            r = rect.inflate(int(26 * a), int(6 * a))
            draw_panel(surf, r, fill=lerp_color((10, 12, 34), (14, 50, 80), a), alpha=int(170 + 60 * a),
                       border=lerp_color((60, 70, 130), color, a), border_alpha=int(150 + 105 * a))
            if a > 0.05:
                draw_glow(surf, (r.left + 6, r.centery), 34, color, 0.7 * a)
                draw_glow(surf, (r.right - 6, r.centery), 34, color, 0.7 * a)
                bounce = math.sin(t * 8) * 3
                draw_text(surf, ">", 24, color, (r.left + 22 + bounce, r.centery))
                draw_text(surf, "<", 24, color, (r.right - 22 - bounce, r.centery))
            draw_text(surf, name, 24, lerp_color(DIM, WHITE, a), r.center, glow=3 if a > 0.5 else 0)


# --------------------------------------------------------------- titles ----
def draw_title(surf, text, size, y, t, c1=CYAN, c2=MAGENTA):
    """Big wavy neon title; every few seconds it glitches."""
    letters = [render_text(ch, size, lerp_color(c1, c2, i / max(1, len(text) - 1)), 5) for i, ch in enumerate(text)]
    gap = int(size * 0.05)
    total = sum(img.get_width() - 20 for img in letters) + gap * (len(text) - 1)
    glitch = (t % 4.0) < 0.18
    x = WIDTH // 2 - total // 2
    for i, img in enumerate(letters):
        yy = y + math.sin(t * 3 + i * 0.55) * 7
        if glitch:
            ghost = img.copy()
            ghost.fill((255, 0, 60, 255), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(ghost, (x - 10 + random.randint(-4, 4), yy - img.get_height() // 2))
        surf.blit(img, (x - 10, yy - img.get_height() // 2))
        x += img.get_width() - 20 + gap


def draw_chase_strip(surf, t, y=640):
    """Decoration: the blob runs across the screen while the bot chases it."""
    span = WIDTH + 300
    blob_x = (t * 150) % span - 150
    bot_x = blob_x - 170
    hop = abs(math.sin(t * 9)) * 6
    stretch = 0.3 * abs(math.sin(t * 9))
    for k in range(int((blob_x - bot_x) // 24)):                  # dotted "BFS" line
        draw_glow(surf, (bot_x + 24 + k * 24, y + 4), 8, YELLOW, 0.6 + 0.4 * math.sin(t * 8 - k))
    draw_bot(surf, bot_x, y, t, rage=0.6)
    draw_blob(surf, blob_x, y, t, (0, 1), stretch, 1.0, hop)


# ------------------------------------------------------------------ HUD ----
def draw_hud(surf, t, level_num, level_total, difficulty, time_left, time_limit, score,
             threat, path_on, level_name):
    chips = [pygame.Rect(40, 14, 150, 66), pygame.Rect(206, 14, 176, 66),
             pygame.Rect(398, 14, 300, 66), pygame.Rect(714, 14, 206, 66)]
    for rect in chips:
        draw_panel(surf, rect, alpha=185, border=(70, 90, 170), border_alpha=170)

    draw_text(surf, "LEVEL", 13, DIM, (chips[0].centerx, chips[0].y + 14))
    draw_text(surf, "%d / %d" % (level_num, level_total), 28, CYAN, (chips[0].centerx, chips[0].y + 42), glow=2)

    dcolor = DIFFICULTIES[difficulty]["color"]
    draw_text(surf, "DIFFICULTY", 13, DIM, (chips[1].centerx, chips[1].y + 14))
    draw_text(surf, difficulty, 28, dcolor, (chips[1].centerx, chips[1].y + 42), glow=2)

    secs = max(0, math.ceil(time_left))
    frac = max(0.0, min(1.0, time_left / time_limit))
    tcolor = GREEN if frac > 0.5 else YELLOW if frac > 0.25 else RED
    panic = secs <= 10 and time_left > 0
    scale = 1.0 + (0.12 * abs(math.sin(t * 8)) if panic else 0)
    draw_text(surf, "TIME", 13, DIM, (chips[2].centerx, chips[2].y + 11))
    draw_text(surf, str(secs), 28, tcolor, (chips[2].centerx, chips[2].y + 36), glow=2, scale=scale)
    bar = pygame.Rect(chips[2].x + 16, chips[2].bottom - 14, chips[2].w - 32, 7)
    pygame.draw.rect(surf, (20, 24, 50), bar, border_radius=4)
    if frac > 0:
        pygame.draw.rect(surf, tcolor, (bar.x, bar.y, int(bar.w * frac), bar.h), border_radius=4)

    draw_text(surf, "SCORE", 13, DIM, (chips[3].centerx, chips[3].y + 14))
    draw_text(surf, "{:,}".format(int(score)), 28, YELLOW, (chips[3].centerx, chips[3].y + 42), glow=2)

    # left panel: controls
    left = pygame.Rect(14, 100, 152, 300)
    draw_panel(surf, left, alpha=150, border=(70, 90, 170), border_alpha=140)
    draw_text(surf, level_name, 13, MAGENTA, (left.centerx, left.y + 22))
    rows = [("W A S D", "MOVE"), ("ARROWS", "MOVE"), ("V", "BFS PATH"), ("R", "RESTART"), ("ESC", "MENU")]
    for i, (key, what) in enumerate(rows):
        yy = left.y + 62 + i * 46
        draw_text(surf, key, 17, CYAN, (left.centerx, yy))
        draw_text(surf, what, 12, DIM, (left.centerx, yy + 17))

    # right panel: threat meter
    right = pygame.Rect(WIDTH - 166, 100, 152, 420)
    draw_panel(surf, right, alpha=150, border=(70, 90, 170), border_alpha=140)
    draw_text(surf, "THREAT", 15, WHITE, (right.centerx, right.y + 24))
    meter = pygame.Rect(right.centerx - 14, right.y + 50, 28, 280)
    pygame.draw.rect(surf, (18, 20, 44), meter, border_radius=8)
    fill_h = int(meter.h * threat)
    if fill_h > 0:
        fill = pygame.Rect(meter.x, meter.bottom - fill_h, meter.w, fill_h)
        pygame.draw.rect(surf, lerp_color(GREEN, RED, threat), fill, border_radius=8)
        draw_glow(surf, (meter.centerx, fill.top), 30, lerp_color(GREEN, RED, threat), 0.6)
    pygame.draw.rect(surf, (90, 100, 170), meter, 2, border_radius=8)
    label = "DANGER!" if threat > 0.7 else "CLOSE" if threat > 0.4 else "SAFE"
    draw_text(surf, label, 16, lerp_color(GREEN, RED, threat), (right.centerx, right.y + 352),
              scale=1 + (0.1 * math.sin(t * 12) if threat > 0.7 else 0))
    draw_text(surf, "BFS PATH", 12, DIM, (right.centerx, right.y + 386))
    draw_text(surf, "ON" if path_on else "OFF", 16, YELLOW if path_on else DIM, (right.centerx, right.y + 404))


# --------------------------------------------------------- HOW AI WORKS ----
MINI_MAZE = ["#########",
             "#E..#...#",
             "#.#.#.#.#",
             "#.#...#.#",
             "#.#####.#",
             "#.....#P#",
             "#########"]
STEPS = ["The maze is a GRID of cells",
         "Every walkable cell is a NODE",
         "Walls are BLOCKED - no links",
         "The enemy is the START node",
         "The player is the TARGET node",
         "BFS explores ring by ring",
         "First hit = the SHORTEST valid path",
         "The enemy follows that route"]


class HowAIDemo:
    """An animated, looping picture of BFS on a tiny maze."""
    CELL = 52
    ORIGIN = (46, 190)

    def __init__(self):
        self.grid = [[1 if ch == "#" else 0 for ch in row] for row in MINI_MAZE]
        self.start = (1, 1)
        self.goal = (5, 7)
        self.explored = []
        self.path = find_path(self.grid, self.start, self.goal, self.explored)
        self.clock = 0.0
        self.per_cell = 0.16
        self.t_grid, self.t_ends = 2.4, 4.4
        self.t_bfs = self.t_ends + len(self.explored) * self.per_cell
        self.t_path = self.t_bfs + 1.8
        self.t_walk = self.t_path + 3.0
        self.t_total = self.t_walk + 1.2

    def update(self, dt):
        self.clock = (self.clock + dt) % self.t_total

    def active_step(self):
        c = self.clock
        if c < self.t_grid:
            return int(c / self.t_grid * 3)          # steps 0..2
        if c < self.t_ends:
            return 3 if c < (self.t_grid + self.t_ends) / 2 else 4
        if c < self.t_bfs:
            return 5
        if c < self.t_path:
            return 6
        return 7

    def center(self, row, col):
        return (self.ORIGIN[0] + col * self.CELL + self.CELL / 2, self.ORIGIN[1] + row * self.CELL + self.CELL / 2)

    def draw(self, surf, t):
        draw_title(surf, "HOW THE AI WORKS", 44, 70, t, YELLOW, MAGENTA)
        draw_text(surf, "Breadth-First Search on a graph", 18, DIM, (WIDTH // 2, 118))
        c = self.clock
        cs = self.CELL
        board = pygame.Rect(self.ORIGIN[0] - 14, self.ORIGIN[1] - 14, cs * 9 + 28, cs * 7 + 28)
        draw_panel(surf, board, alpha=170, border=(70, 90, 170))

        revealed = 0
        if c > self.t_ends:
            revealed = min(len(self.explored), int((c - self.t_ends) / self.per_cell) + 1)
        order = {cell: i + 1 for i, cell in enumerate(self.explored[:revealed])}

        for row in range(7):
            for col in range(9):
                x, y = self.center(row, col)
                if self.grid[row][col] == 1:
                    pygame.draw.rect(surf, (30, 24, 70), (x - cs / 2 + 3, y - cs / 2 + 3, cs - 6, cs - 6), border_radius=8)
                    pygame.draw.rect(surf, (110, 40, 150), (x - cs / 2 + 3, y - cs / 2 + 3, cs - 6, cs - 6), 1, border_radius=8)
                    continue
                if c > self.t_grid * 0.34:            # edges appear with the nodes
                    for d_row, d_col in ((0, 1), (1, 0)):
                        r2, c2 = row + d_row, col + d_col
                        if r2 < 7 and c2 < 9 and self.grid[r2][c2] == 0:
                            x2, y2 = self.center(r2, c2)
                            visited = (row, col) in order and (r2, c2) in order
                            pygame.draw.line(surf, (0, 200, 240) if visited else (50, 66, 130), (x, y), (x2, y2), 3)

        for row in range(7):
            for col in range(9):
                if self.grid[row][col] == 1:
                    continue
                x, y = self.center(row, col)
                cell = (row, col)
                if c > self.t_grid * 0.17:
                    if cell in order:
                        k = order[cell]
                        fresh = revealed - k < 3
                        color = lerp_color((0, 230, 255), (190, 90, 255), k / len(self.explored))
                        if fresh:
                            draw_glow(surf, (x, y), 30, color, 0.9)
                        pygame.draw.circle(surf, color, (int(x), int(y)), 15)
                        draw_text(surf, str(k), 15, (10, 10, 30), (x, y))
                    else:
                        pygame.draw.circle(surf, (24, 30, 70), (int(x), int(y)), 14)
                        pygame.draw.circle(surf, (90, 110, 200), (int(x), int(y)), 14, 2)

        if c > self.t_bfs:                            # the shortest path lights up
            shown = min(len(self.path), int((c - self.t_bfs) / 1.4 * len(self.path)) + 1)
            pts = [self.center(*cell) for cell in self.path[:shown]]
            if len(pts) > 1:
                pygame.draw.lines(surf, (255, 215, 60), False, pts, 5)
            for p in pts:
                draw_glow(surf, p, 18, YELLOW, 0.8)

        # start (enemy) and target (player)
        sx, sy = self.center(*self.start)
        gx, gy = self.center(*self.goal)
        if c > self.t_grid:
            ex, ey = sx, sy
            if c > self.t_path:
                k = min(1.0, (c - self.t_path) / (self.t_walk - self.t_path))
                pos = k * (len(self.path) - 1)
                i = min(len(self.path) - 2, int(pos))
                a, b = self.center(*self.path[i]), self.center(*self.path[i + 1])
                f = pos - i
                ex, ey = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            draw_bot(surf, ex, ey + 4, t, 0.3, 0.8)
            draw_blob(surf, gx, gy, t, (0, -1), 0.0, 0.85)
            draw_text(surf, "START", 12, RED, (sx, sy - 32))
            draw_text(surf, "TARGET", 12, CYAN, (gx, gy - 32))

        # step list
        active = self.active_step()
        panel = pygame.Rect(560, 170, 372, 420)
        draw_panel(surf, panel, alpha=170, border=(70, 90, 170))
        for i, text in enumerate(STEPS):
            y = panel.y + 34 + i * 49
            on = i == active
            done = i < active
            color = YELLOW if on else WHITE if done else (80, 90, 140)
            if on:
                draw_glow(surf, (panel.x + 40, y), 40, YELLOW, 0.5)
            pygame.draw.circle(surf, color, (panel.x + 34, y), 15, 0 if on else 2)
            draw_text(surf, str(i + 1), 17, (10, 10, 30) if on else color, (panel.x + 34, y))
            draw_text(surf, text, 17, color, (panel.x + 62, y), anchor="midleft")
        draw_text(surf, "Time: O(V + E)  -  at most 225 cells, under 1 ms", 15, DIM, (panel.centerx, panel.bottom + 26))
