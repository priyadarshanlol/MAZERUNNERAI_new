"""Unit tests for the BFS pathfinder.  Run:  python -m unittest test_bfs -v"""
import unittest
from pathfinding import find_path

OPEN_ROOM = [[1, 1, 1, 1, 1],
             [1, 0, 0, 0, 1],
             [1, 0, 0, 0, 1],
             [1, 0, 0, 0, 1],
             [1, 1, 1, 1, 1]]

WALL_IN_MIDDLE = [[1, 1, 1, 1, 1],
                  [1, 0, 1, 0, 1],
                  [1, 0, 1, 0, 1],
                  [1, 0, 0, 0, 1],
                  [1, 1, 1, 1, 1]]

SEALED = [[1, 1, 1, 1, 1],
          [1, 0, 1, 0, 1],
          [1, 1, 1, 1, 1]]


def is_valid(maze, path):
    """Every step must be on a floor cell and exactly one cell away."""
    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        if abs(r1 - r2) + abs(c1 - c2) != 1:
            return False
    return all(maze[r][c] == 0 for r, c in path)


class TestBFS(unittest.TestCase):
    def test_straight_path(self):
        path = find_path(OPEN_ROOM, (1, 1), (1, 3))
        self.assertEqual(path, [(1, 1), (1, 2), (1, 3)])

    def test_shortest_in_open_room(self):
        path = find_path(OPEN_ROOM, (1, 1), (3, 3))
        self.assertEqual(len(path), 5)          # 4 moves + the start cell
        self.assertTrue(is_valid(OPEN_ROOM, path))

    def test_goes_around_wall(self):
        path = find_path(WALL_IN_MIDDLE, (1, 1), (1, 3))
        self.assertEqual(path[0], (1, 1))
        self.assertEqual(path[-1], (1, 3))
        self.assertIn((3, 2), path)             # had to walk round the bottom
        self.assertTrue(is_valid(WALL_IN_MIDDLE, path))

    def test_no_path_returns_empty_list(self):
        self.assertEqual(find_path(SEALED, (1, 1), (1, 3)), [])

    def test_start_equals_goal(self):
        self.assertEqual(find_path(OPEN_ROOM, (2, 2), (2, 2)), [(2, 2)])

    def test_start_or_goal_in_wall(self):
        self.assertEqual(find_path(OPEN_ROOM, (0, 0), (1, 1)), [])
        self.assertEqual(find_path(OPEN_ROOM, (1, 1), (0, 0)), [])

    def test_outside_the_grid(self):
        self.assertEqual(find_path(OPEN_ROOM, (1, 1), (9, 9)), [])
        self.assertEqual(find_path(OPEN_ROOM, (-1, 1), (1, 1)), [])

    def test_explored_list_is_filled(self):
        explored = []
        find_path(OPEN_ROOM, (1, 1), (3, 3), explored)
        self.assertEqual(explored[0], (1, 1))
        self.assertIn((3, 3), explored)


if __name__ == "__main__":
    unittest.main()
