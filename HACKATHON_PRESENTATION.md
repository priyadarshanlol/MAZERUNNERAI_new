# 5-slide deck

**Slide 1 - Problem Statement**: Build a maze game where an enemy chases the player using BFS or A*. Must navigate walls, have win and lose conditions.

**Slide 2 - Solution / Architecture**: Python + Pygame. Modules: main (loop/states), maze, player, enemy, pathfinding (BFS), levels, ui, particles. Flow: input -> player -> BFS -> enemy -> collisions -> draw.

**Slide 3 - BFS / AI**: Maze = graph (cells = nodes). Queue + visited + parent map. Shortest path in O(V+E). Enemy recalculates every few hundred ms. Show the "How AI works" screen.

**Slide 4 - Features + Tech + Demo**: 3 levels, 3 difficulties, timer, score, BFS visualiser (V), neon visuals and particles. Tech: Python 3, Pygame, standard library, Git.

**Slide 5 - Challenges + Future Scope**: Challenges - smooth movement vs grid logic, fair enemy speed, verifying every level is solvable (automated tests). Future - A*, random mazes, power-ups, multiple enemies.

# 3-5 minute demo script
1. Open the game, show the menu. 2. Select difficulty (MEDIUM). 3. Start - point at the glowing yellow BFS path from enemy to player. 4. Move so the enemy has to go around a wall - the path re-routes. 5. Press `V` to hide/show the path. 6. Show the threat meter and danger glow. 7. Reach the portal -> victory, show score. 8. Replay on HARD and let it catch you -> game over. 9. Open HOW AI WORKS and explain the numbered nodes.
