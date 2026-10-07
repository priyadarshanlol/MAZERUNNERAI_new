"""main.py - game loop and game states.

States:  MENU -> DIFFICULTY / HOW_AI / PLAYING -> VICTORY or GAME_OVER -> ...
Inside PLAYING there are phases:  ready (3-2-1)  ->  play  ->  win / dead
Run with:  python main.py
"""
import math
import random
import pygame

from settings import *
import ui
from sounds import Sounds
from maze import Maze
from player import Player
from enemy import Enemy
from levels import LEVELS, load_level
from particles import ParticleSystem, draw_glow

KEY_DIRECTIONS = {
    pygame.K_w: (-1, 0), pygame.K_UP: (-1, 0),
    pygame.K_s: (1, 0), pygame.K_DOWN: (1, 0),
    pygame.K_a: (0, -1), pygame.K_LEFT: (0, -1),
    pygame.K_d: (0, 1), pygame.K_RIGHT: (0, 1),
}


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("MAZE RUNNER - AI ESCAPE CHALLENGE")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.veil = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.sound = Sounds()
        self.background = ui.Background()
        self.fx = ui.ScreenFX()
        self.particles = ParticleSystem()
        self.how_ai = ui.HowAIDemo()

        self.main_menu = ui.Menu(["START GAME", "SELECT DIFFICULTY", "HOW AI WORKS", "QUIT"],
                                 WIDTH // 2, 290, sound=self.sound)
        self.diff_menu = ui.Menu(DIFFICULTY_NAMES + ["BACK"], WIDTH // 2, 230, sound=self.sound)
        self.back_menu = ui.Menu(["BACK"], WIDTH // 2, 652, width=240, height=46, sound=self.sound)
        self.result_menu = None

        self.running = True
        self.time = 0.0
        self.state = "MENU"
        self.difficulty = "MEDIUM"
        self.level_index = 0
        self.total_score = 0
        self.score_before = 0
        self.display_score = 0
        self.show_path = SHOW_BFS_PATH
        self.held = []
        self.fade = 255.0
        self.shake = 0.0
        self.flash = 0.0
        self.go_flash = 0.0
        self.phase = "ready"
        self.phase_time = 0.0
        self.last_count = 0
        self.dead_reason = ""
        self.player_hidden = False
        self.level_points = 0
        self.time_taken = 0.0
        self.win_from = (0, 0)
        self.time_left = 0.0
        self.time_limit = 1
        self.maze = self.player = self.enemy = None

    # ======================================================== state changes ==
    def change_state(self, state):
        self.state = state
        self.fade = 255.0
        self.held.clear()

    def go_menu(self):
        self.particles.clear()
        self.change_state("MENU")

    def start_level(self):
        """Build the maze, player and enemy for the current level + difficulty."""
        level = load_level(self.level_index)
        settings = DIFFICULTIES[self.difficulty]
        self.maze = Maze(level)
        self.player = Player(level["player_start"])
        self.enemy = Enemy(level["enemy_start"], settings["enemy_step_ms"], settings["recalc_ms"])
        self.enemy.recalculate(self.maze, self.player.cell)     # path is visible from the start
        self.time_limit = settings["time_limit"]
        self.time_left = float(self.time_limit)
        self.score_before = self.total_score
        self.phase, self.phase_time, self.last_count = "ready", 0.0, 0
        self.player_hidden = False
        self.go_flash = self.flash = self.shake = 0.0
        self.particles.clear()
        self.change_state("PLAYING")

    def restart_level(self):
        self.total_score = self.score_before
        self.start_level()

    def start_win(self):
        self.phase, self.phase_time = "win", 0.0
        self.win_from = self.player.pixel()
        remaining = max(0, int(self.time_left))
        self.level_points = remaining * 10 + 100          # score = time left x10 + 100 bonus
        self.total_score = self.score_before + self.level_points
        self.time_taken = self.time_limit - self.time_left
        ex, ey = self.maze.cell_to_pixel(*self.maze.exit)
        self.particles.confetti(ex, ey, 90, 30)
        self.particles.burst(ex, ey, (120, 255, 200), 40, 260)
        self.sound.play("win")

    def start_dead(self, reason):
        self.phase, self.phase_time = "dead", 0.0
        self.dead_reason = reason
        self.player_hidden = True
        self.time_taken = self.time_limit - self.time_left
        px, py = self.player.pixel()
        self.particles.burst(px, py, CYAN, 70, 380)
        self.particles.burst(px, py, (255, 255, 255), 25, 200)
        self.shake, self.flash = 24.0, 1.0
        self.held.clear()
        self.sound.play("lose")

    def show_result(self, victory):
        if victory:
            has_next = self.level_index + 1 < len(LEVELS)
            options = (["NEXT LEVEL"] if has_next else []) + ["REPLAY", "MAIN MENU", "QUIT"]
        else:
            options = ["PLAY AGAIN", "MAIN MENU", "QUIT"]
        self.result_menu = ui.Menu(options, WIDTH // 2, 392, 300, 44, 10, sound=self.sound)
        self.display_score = self.score_before
        self.change_state("VICTORY" if victory else "GAME_OVER")

    # ================================================================ events ==
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.state == "MENU":
                self.event_menu(event)
            elif self.state == "DIFFICULTY":
                self.event_difficulty(event)
            elif self.state == "HOW_AI":
                self.event_how_ai(event)
            elif self.state == "PLAYING":
                self.event_playing(event)
            else:
                self.event_result(event)

    def event_menu(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
            return
        choice = self.main_menu.handle(event)
        if choice:
            self.sound.play("confirm")
        if choice == "START GAME":
            self.level_index, self.total_score = 0, 0
            self.start_level()
        elif choice == "SELECT DIFFICULTY":
            self.diff_menu.selected = DIFFICULTY_NAMES.index(self.difficulty)
            self.change_state("DIFFICULTY")
        elif choice == "HOW AI WORKS":
            self.how_ai.clock = 0.0
            self.change_state("HOW_AI")
        elif choice == "QUIT":
            self.running = False

    def event_difficulty(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.change_state("MENU")
            return
        choice = self.diff_menu.handle(event)
        if choice:
            self.sound.play("confirm")
            if choice in DIFFICULTIES:
                self.difficulty = choice
            self.change_state("MENU")

    def event_how_ai(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.change_state("MENU")
            return
        if self.back_menu.handle(event):
            self.sound.play("confirm")
            self.change_state("MENU")

    def event_playing(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.go_menu()
            elif event.key == pygame.K_v:
                self.show_path = not self.show_path
            elif event.key == pygame.K_r:
                self.restart_level()
            elif event.key in KEY_DIRECTIONS:
                direction = KEY_DIRECTIONS[event.key]
                if direction in self.held:
                    self.held.remove(direction)
                self.held.append(direction)         # newest key wins
        elif event.type == pygame.KEYUP and event.key in KEY_DIRECTIONS:
            direction = KEY_DIRECTIONS[event.key]
            if direction in self.held and not any(
                    KEY_DIRECTIONS[k] == direction and pygame.key.get_pressed()[k] for k in KEY_DIRECTIONS):
                self.held.remove(direction)

    def event_result(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.go_menu()
            return
        choice = self.result_menu.handle(event)
        if not choice:
            return
        self.sound.play("confirm")
        if choice == "NEXT LEVEL":
            self.level_index += 1
            self.start_level()
        elif choice in ("REPLAY", "PLAY AGAIN"):
            self.restart_level()
        elif choice == "MAIN MENU":
            self.go_menu()
        elif choice == "QUIT":
            self.running = False

    # =============================================================== updates ==
    def update(self, dt):
        self.time += dt
        self.particles.update(dt)
        self.fade = max(0.0, self.fade - 700 * dt)
        self.shake = self.shake * (0.02 ** dt) if self.shake > 0.3 else 0.0
        self.flash = max(0.0, self.flash - dt * 2.5)
        self.go_flash = max(0.0, self.go_flash - dt * 1.6)

        if self.state == "MENU":
            self.main_menu.update(dt)
        elif self.state == "DIFFICULTY":
            self.diff_menu.update(dt)
        elif self.state == "HOW_AI":
            self.how_ai.update(dt)
            self.back_menu.update(dt)
        elif self.state == "PLAYING":
            self.update_playing(dt)
        else:
            self.result_menu.update(dt)
            target = self.total_score if self.state == "VICTORY" else self.score_before
            self.display_score += (target - self.display_score) * min(1.0, dt * 4)
            if abs(target - self.display_score) < 1:
                self.display_score = target
            if self.state == "VICTORY" and random.random() < dt * 35:      # confetti rain
                self.particles.add(random.uniform(0, WIDTH), -10, random.uniform(-40, 40), random.uniform(60, 160),
                                   4.5, random.uniform(6, 11),
                                   random.choice([(255, 60, 120), CYAN, YELLOW, (120, 255, 150), (200, 120, 255)]),
                                   gravity=40, kind="confetti")

    def caught(self):
        if self.player.cell == self.enemy.cell:
            return True
        p_row, p_col = self.player.visual()
        e_row, e_col = self.enemy.visual()
        return math.hypot(p_row - e_row, p_col - e_col) < CATCH_DISTANCE

    def update_playing(self, dt):
        ms = dt * 1000
        self.phase_time += dt

        if self.phase == "ready":
            remaining = READY_SECONDS - self.phase_time
            count = math.ceil(remaining)
            if remaining <= 0:
                self.phase, self.phase_time, self.go_flash = "play", 0.0, 1.0
                self.sound.play("go")
            elif count != self.last_count:
                self.last_count = count
                self.sound.play("beep")

        elif self.phase == "play":
            wanted = self.held[-1] if self.held else None
            result = self.player.update(ms, wanted, self.maze)
            px, py = self.player.pixel()
            if result == "moved":
                self.particles.dust(px, py + 12, 3)
                self.sound.play("step")
            elif result == "bumped":
                self.particles.dust(px + self.player.facing[1] * 16, py + self.player.facing[0] * 16, 5, CYAN)
                self.sound.play("bump")
                self.shake = max(self.shake, 3.0)

            if self.player.cell == self.maze.exit:       # win check first
                self.start_win()
                return
            self.enemy.update(ms, self.maze, self.player.cell)
            self.time_left -= dt
            if self.caught():
                self.start_dead("THE AI CAUGHT YOU!")
            elif self.time_left <= 0:
                self.time_left = 0.0
                self.start_dead("TIME'S UP!")

        elif self.phase == "win":
            ex, ey = self.maze.cell_to_pixel(*self.maze.exit)
            self.particles.swirl(ex, ey, (150, 255, 220))
            self.player.update(ms, None, self.maze)
            if self.phase_time >= 1.5:
                self.show_result(True)

        elif self.phase == "dead":
            if self.phase_time >= 1.7:
                self.show_result(False)

    # ================================================================ drawing ==
    def threat(self):
        """0 (far away) .. 1 (right behind you), from the length of the BFS path."""
        if not self.enemy.path:
            return 0.0
        return clamp(1 - (len(self.enemy.path) - 1) / 20)

    def draw_scene(self, c):
        t = self.time
        self.background.draw(c, t)
        self.maze.draw_base(c, t)

        c.set_clip(pygame.Rect(MAZE_X, MAZE_Y, MAZE_PX, MAZE_PX))     # light pools on the maze
        if not self.player_hidden:
            draw_glow(c, self.player.pixel(), 150, CYAN, 0.40)
        draw_glow(c, self.enemy.pixel(), 170, (255, 30, 60), 0.35 + 0.25 * self.threat())
        c.set_clip(None)

        if self.show_path:
            self.enemy.draw_path(c, t)

        win_p = clamp(self.phase_time / 1.2) if self.phase == "win" else 0.0
        self.maze.draw_exit(c, t, 1.0 + 0.5 * math.sin(win_p * math.pi) if self.phase == "win" else 1.0)
        self.enemy.draw(c, t, self.threat())

        if self.phase == "win" and win_p < 1:
            ease = win_p * win_p * (3 - 2 * win_p)
            ex, ey = self.maze.cell_to_pixel(*self.maze.exit)
            pos = (self.win_from[0] + (ex - self.win_from[0]) * ease, self.win_from[1] + (ey - self.win_from[1]) * ease)
            self.player.draw(c, t, pos, max(0.05, 1 - ease))
        elif not self.player_hidden and self.phase != "win":
            self.player.draw(c, t)

        if self.state == "PLAYING":
            self.particles.draw(c)
        score = self.score_before + max(0, int(self.time_left)) * 10 if self.state == "PLAYING" else self.display_score
        ui.draw_hud(c, t, self.level_index + 1, len(LEVELS), self.difficulty, self.time_left, self.time_limit,
                    score, self.threat(), self.show_path, self.maze.name)
        if self.state == "PLAYING":
            self.draw_overlays(c)

    def draw_overlays(self, c):
        center = (MAZE_X + MAZE_PX // 2, MAZE_Y + MAZE_PX // 2)
        if self.phase == "ready":
            remaining = READY_SECONDS - self.phase_time
            count = max(1, math.ceil(remaining))
            k = 1 - (remaining - (count - 1))                       # 0 -> 1 during each second
            color = {3: RED, 2: YELLOW, 1: GREEN}.get(count, WHITE)
            ui.draw_text(c, "LEVEL %d  -  %s" % (self.level_index + 1, self.maze.name), 28, WHITE,
                         (center[0], center[1] - 120), glow=3)
            ui.draw_text(c, "GET READY", 18, DIM, (center[0], center[1] - 90))
            ui.draw_text(c, str(count), 130, color, center, glow=6, scale=1.7 - 0.7 * (1 - (1 - k) ** 3),
                         alpha=int(255 * (1 - 0.5 * k)))
        if self.go_flash > 0:
            ui.draw_text(c, "GO!", 130, GREEN, center, glow=6, scale=1 + (1 - self.go_flash) * 1.6,
                         alpha=int(255 * self.go_flash))
        if self.phase == "dead":
            ui.draw_text(c, self.dead_reason, 40, RED, center, glow=5,
                         alpha=int(255 * clamp(self.phase_time * 2)))

    def draw_modal(self, c):
        victory = self.state == "VICTORY"
        panel = pygame.Rect(WIDTH // 2 - 250, 110, 500, self.result_menu.rects[-1].bottom + 32 - 110)
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 10, 150))
        c.blit(veil, (0, 0))
        color = GREEN if victory else RED
        ui.draw_panel(c, panel, alpha=225, border=color, border_alpha=230, width=3, radius=20)
        draw_glow(c, (panel.centerx, panel.top), 160, color, 0.35)
        if victory:
            ui.draw_text(c, "YOU ESCAPED!", 52, GREEN, (panel.centerx, 165), glow=6)
            last = self.level_index + 1 >= len(LEVELS)
            ui.draw_text(c, "ALL LEVELS CLEARED - YOU BEAT THE AI!" if last else "THE AI LOST YOUR TRAIL",
                         18, YELLOW if last else DIM, (panel.centerx, 210))
            time_label = "TIME TAKEN"
        else:
            ui.draw_text(c, "GAME OVER", 52, RED, (panel.centerx, 165), glow=6)
            ui.draw_text(c, "TIME'S UP!" if self.dead_reason.startswith("TIME") else "THE AI CAUGHT YOU!",
                         24, WHITE, (panel.centerx, 210))
            time_label = "TIME SURVIVED"
        ui.draw_text(c, "LEVEL %d / %d  -  %s  -  %s" % (self.level_index + 1, len(LEVELS), self.maze.name, self.difficulty),
                     16, DIM, (panel.centerx, 250))
        ui.draw_text(c, "%s   %.1f s" % (time_label, self.time_taken), 22, WHITE, (panel.centerx, 287))
        ui.draw_text(c, "SCORE  {:,}".format(int(self.display_score)), 38, YELLOW, (panel.centerx, 337), glow=4)
        self.result_menu.draw(c, self.time, color)

    def draw_menu_screen(self, c):
        t = self.time
        self.background.draw(c, t)
        ui.draw_title(c, "MAZE RUNNER", 86, 125, t)
        ui.draw_text(c, "AI  ESCAPE  CHALLENGE", 26, MAGENTA if int(t * 3) % 2 else CYAN, (WIDTH // 2, 215), glow=3,
                     alpha=120 if (t % 5) < 0.08 else 255)
        self.main_menu.draw(c, t)
        color = DIFFICULTIES[self.difficulty]["color"]
        ui.draw_text(c, "DIFFICULTY:  %s" % self.difficulty, 18, color, (WIDTH // 2, 566), glow=2)
        ui.draw_chase_strip(c, t, 645)

    def draw_difficulty_screen(self, c):
        t = self.time
        self.background.draw(c, t)
        ui.draw_title(c, "SELECT DIFFICULTY", 54, 110, t, GREEN, RED)
        self.diff_menu.draw(c, t)
        choice = self.diff_menu.options[self.diff_menu.selected]
        if choice in DIFFICULTIES:
            info = DIFFICULTIES[choice]
            panel = pygame.Rect(WIDTH // 2 - 250, 520, 500, 150)
            ui.draw_panel(c, panel, alpha=185, border=info["color"])
            ui.draw_text(c, info["blurb"], 22, info["color"], (panel.centerx, panel.y + 30), glow=2)
            for i, (label, value) in enumerate((("ENEMY SPEED", 170 / info["enemy_step_ms"]),
                                                ("TIME PRESSURE", 30 / info["time_limit"]))):
                y = panel.y + 74 + i * 36
                ui.draw_text(c, label, 15, DIM, (panel.x + 30, y), anchor="midleft")
                bar = pygame.Rect(panel.x + 190, y - 8, 270, 16)
                pygame.draw.rect(c, (20, 24, 50), bar, border_radius=8)
                pygame.draw.rect(c, info["color"], (bar.x, bar.y, int(bar.w * value), bar.h), border_radius=8)
        else:
            ui.draw_text(c, "CURRENT:  %s" % self.difficulty, 20, DIFFICULTIES[self.difficulty]["color"],
                         (WIDTH // 2, 580), glow=2)

    def draw(self):
        c = self.canvas
        danger = 0.0
        if self.state in ("PLAYING", "VICTORY", "GAME_OVER"):
            self.draw_scene(c)
            if self.state == "PLAYING" and self.phase == "play":
                danger = clamp(1 - (len(self.enemy.path) - 1) / 7) * 0.9 if self.enemy.path else 0.0
            if self.state != "PLAYING":
                self.draw_modal(c)
                self.particles.draw(c)
        elif self.state == "MENU":
            self.draw_menu_screen(c)
        elif self.state == "DIFFICULTY":
            self.draw_difficulty_screen(c)
        elif self.state == "HOW_AI":
            self.background.draw(c, self.time)
            self.how_ai.draw(c, self.time)
            self.back_menu.draw(c, self.time)
        if self.flash > 0:
            c.fill((int(190 * self.flash), 0, int(30 * self.flash)), special_flags=pygame.BLEND_RGB_ADD)
        self.fx.apply(c, danger, self.time)

        self.screen.fill((0, 0, 0))
        s = self.shake
        self.screen.blit(c, (random.uniform(-s, s), random.uniform(-s, s)) if s else (0, 0))
        if self.fade > 0:
            self.veil.set_alpha(int(self.fade))
            self.screen.blit(self.veil, (0, 0))
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)      # cap so a lag spike can't teleport things
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
