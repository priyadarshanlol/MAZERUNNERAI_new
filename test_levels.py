"""Checks every level.  Run:  python -m unittest test_levels -v"""
import unittest
from levels import LEVELS, load_level
from pathfinding import find_path
from settings import GRID_SIZE


class TestLevels(unittest.TestCase):
    def test_there_are_three_levels(self):
        self.assertGreaterEqual(len(LEVELS), 3)

    def test_every_level(self):
        for index in range(len(LEVELS)):
            level = load_level(index)
            grid = level["grid"]
            with self.subTest(level=index + 1):
                self.assertEqual(len(grid), GRID_SIZE)
                self.assertTrue(all(len(row) == GRID_SIZE for row in grid))
                # solid border so nobody can walk out of the maze
                for i in range(GRID_SIZE):
                    for r, c in ((0, i), (GRID_SIZE - 1, i), (i, 0), (i, GRID_SIZE - 1)):
                        self.assertEqual(grid[r][c], 1)
                for key in ("player_start", "enemy_start", "exit"):
                    r, c = level[key]
                    self.assertEqual(grid[r][c], 0, key + " is inside a wall")
                self.assertNotEqual(level["player_start"], level["enemy_start"])
                # the player can reach the exit, and the enemy can reach the player
                self.assertTrue(find_path(grid, level["player_start"], level["exit"]))
                self.assertTrue(find_path(grid, level["enemy_start"], level["player_start"]))

    def test_missing_level_raises(self):
        with self.assertRaises(IndexError):
            load_level(99)


if __name__ == "__main__":
    unittest.main()
