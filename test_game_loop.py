"""Headless integration tests (no window needed).  Run:  python -m unittest test_game_loop -v"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import unittest
from main import Game
from pathfinding import find_path
from settings import DIFFICULTY_NAMES, TILE

DT = 1 / 60


class TestGameLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = Game()

    def start(self, level=0, difficulty="MEDIUM"):
        g = self.game
        g.level_index, g.difficulty, g.total_score = level, difficulty, 0
        g.start_level()
        for _ in range(190):                       # skip the 3-2-1 countdown
            g.update(DT)
        self.assertEqual(g.phase, "play")
        return g

    def play_until_over(self, g, bot, seconds=70):
        for _ in range(int(seconds * 60)):
            if g.state != "PLAYING":
                break
            bot(g)
            before = g.enemy.pixel()
            g.update(DT)
            after = g.enemy.pixel()
            self.assertTrue(g.maze.is_walkable(g.enemy.cell), "enemy inside a wall")
            self.assertTrue(g.maze.is_walkable(g.player.cell), "player inside a wall")
            jump = ((after[0] - before[0]) ** 2 + (after[1] - before[1]) ** 2) ** 0.5
            self.assertLess(jump, TILE, "enemy teleported")
        g.draw()

    @staticmethod
    def exit_bot(g):
        path = find_path(g.maze.grid, g.player.cell, g.maze.exit)
        if len(path) > 1:
            g.held = [(path[1][0] - g.player.cell[0], path[1][1] - g.player.cell[1])]

    def test_player_reaches_exit_on_every_level_and_difficulty(self):
        for level in range(3):
            for diff in DIFFICULTY_NAMES:
                with self.subTest(level=level + 1, difficulty=diff):
                    g = self.start(level, diff)
                    self.play_until_over(g, self.exit_bot)
                    self.assertEqual(g.state, "VICTORY")
                    self.assertGreater(g.total_score, 100)

    def test_standing_still_gets_you_caught(self):
        g = self.start(0, "HARD")
        self.play_until_over(g, lambda game: None)
        self.assertEqual(g.state, "GAME_OVER")
        self.assertIn("CAUGHT", g.dead_reason)

    def test_timer_runs_out(self):
        g = self.start(0, "EASY")
        g.enemy.step_ms = 10 ** 9                   # frozen enemy so only the clock can end it
        g.enemy.step_timer = 10 ** 9
        self.play_until_over(g, lambda game: None, seconds=70)
        self.assertEqual(g.state, "GAME_OVER")
        self.assertIn("TIME", g.dead_reason)

    def test_walls_and_edges_block_the_player(self):
        g = self.start(0, "EASY")
        g.enemy.step_timer = 10 ** 9
        start = g.player.cell
        g.held = [(-1, 0)]                          # start is (1,1): up is the border wall
        for _ in range(60):
            g.update(DT)
        self.assertEqual(g.player.cell, start)

    def test_restart_and_menu(self):
        g = self.start(1, "MEDIUM")
        g.restart_level()
        self.assertEqual(g.state, "PLAYING")
        self.assertEqual(g.phase, "ready")
        g.go_menu()
        self.assertEqual(g.state, "MENU")

    def test_all_screens_draw(self):
        g = self.game
        for state in ("MENU", "DIFFICULTY", "HOW_AI"):
            g.state = state
            g.update(DT)
            g.draw()


if __name__ == "__main__":
    unittest.main()
