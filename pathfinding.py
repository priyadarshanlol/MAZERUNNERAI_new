"""pathfinding.py - Breadth-First Search (BFS) on the maze grid.

The maze is treated as an UNWEIGHTED GRAPH:
    node  = a walkable cell  (grid value 0)
    edge  = a link between two neighbouring walkable cells (up/down/left/right)
    wall  = a blocked node   (grid value 1) - BFS never enters it

Because every step costs the same (1), BFS is guaranteed to find the
SHORTEST path.  This is the ONLY pathfinding code in the project.
"""
from collections import deque

# The four moves allowed: (row change, column change)
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def find_path(maze, start, goal, explored=None):
    """Return the shortest path from start to goal as a list of (row, col).

    maze     : 2D list, 1 = wall, 0 = walkable
    start    : (row, col) - the enemy position
    goal     : (row, col) - the player position
    explored : optional list; if given, every cell BFS visits is appended
               to it (in visiting order) so the game can animate the search.

    The returned path includes both start and goal.
    Returns []  if start/goal is invalid or no route exists.
    Returns [start] if start == goal.
    """
    rows = len(maze)
    cols = len(maze[0]) if rows else 0

    def walkable(cell):
        row, col = cell
        return 0 <= row < rows and 0 <= col < cols and maze[row][col] == 0

    if not walkable(start) or not walkable(goal):
        return []
    if start == goal:
        return [start]

    queue = deque([start])      # FIFO queue: oldest cell is explored first
    visited = {start}           # cells we already queued (prevents loops)
    parent = {}                 # parent[child] = the cell we came from

    while queue:
        current = queue.popleft()
        if explored is not None:
            explored.append(current)

        if current == goal:
            # Walk backwards goal -> start using the parent links, then flip.
            path = [current]
            while current != start:
                current = parent[current]
                path.append(current)
            path.reverse()
            return path

        for d_row, d_col in DIRECTIONS:
            neighbour = (current[0] + d_row, current[1] + d_col)
            if walkable(neighbour) and neighbour not in visited:
                visited.add(neighbour)
                parent[neighbour] = current
                queue.append(neighbour)

    return []   # queue ran empty: the goal is unreachable
