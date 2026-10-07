# Examiner Q&A (simple answers)

1. **What is BFS?** Breadth-First Search explores a graph level by level: all cells 1 step away, then 2 steps, and so on, using a queue.
2. **Why BFS?** Our maze is an unweighted grid - every move costs the same. BFS guarantees the shortest path in an unweighted graph.
3. **Why not DFS?** DFS goes deep first and finds *a* path, not the shortest one. The enemy would take silly detours.
4. **Why not machine learning?** The problem is small and fully known; BFS is exact, instant (under 1 ms), needs no training data, and is easy to explain.
5. **What is a node?** Each walkable cell (`grid[r][c] == 0`).
6. **What is the graph?** Walkable cells are nodes; neighbouring walkable cells (up/down/left/right) are connected by edges.
7. **How are walls represented?** `1` in the 2D list. BFS and the player both refuse to enter a `1`.
8. **How does the enemy find the player?** Every 200-450 ms (`recalc_ms`) it calls `find_path(grid, enemy_cell, player_cell)` and walks the returned path one cell at a time.
9. **How is the shortest path rebuilt?** While exploring we store `parent[neighbour] = current`. At the goal we follow parents back to the start, then reverse the list.
10. **What if there is no path?** `find_path` returns `[]`; the enemy simply waits and tries again.
11. **Time complexity?** O(V + E). V <= 225 cells, E <= 4V, so it runs in well under a millisecond. Space O(V).
12. **How does player collision work?** Before moving we check `maze.is_walkable(target)` - inside the grid and value 0. Otherwise the player bumps and stays.
13. **How does enemy collision (catching) work?** The enemy is caught-you when it is on your cell or closer than 0.55 cell to you on screen.
14. **How does the timer work?** `time_left -= dt` every frame (dt from the Pygame clock). At 0 the game goes to GAME OVER ("TIME'S UP").
15. **What would you improve?** A* for bigger maps, random maze generation, power-ups, several enemies, level editor.
