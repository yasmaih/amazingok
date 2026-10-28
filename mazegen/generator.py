"""Maze generator: builds the walls of a maze, with no print and no file."""

import random
from collections import deque

# Move of one cell for each direction, as (dx, dy). y grows downwards.
DIRECTIONS = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}

# The same wall seen from the neighbour cell.
OPPOSITE = {"N": "S", "E": "W", "S": "N", "W": "E"}

# The "42" drawn with fully closed cells (#). 7 columns x 5 rows.
# Column 3 is empty: it is the centre of the maze, where Pac-Man starts.
PATTERN_42 = [
    "#.#.###",
    "#.#...#",
    "###.###",
    "..#.#..",
    "..#.###",
]

# Pac-Man mode: how many mazes we try before saying the size is too small.
MAX_TRIES = 20


class MazeGenerator:
    """Generate a maze stored as walls[y][x]["N"] (True = wall closed).

    Example:
        gen = MazeGenerator(width=20, height=15, entry_pos=(0, 0),
                            exit_pos=(19, 14), seed=42)
        gen.generate()
        gen.walls[0][0]["E"]   # True if the east wall of (0, 0) is closed
        gen.solve((0, 0), (19, 14))   # shortest path, like "EESSW..."
    """

    def __init__(self, width: int, height: int, entry_pos: tuple[int, int],
                 exit_pos: tuple[int, int], perfect: bool = False,
                 seed: int | None = None) -> None:
        """Store the settings. Nothing is generated before generate().

        Args:
            width: number of columns.
            height: number of rows.
            entry_pos: entry cell (x, y).
            exit_pos: exit cell (x, y).
            perfect: True for exactly one path between any two cells.
            seed: same seed gives the same maze; None gives a new one.
        """
        self.width = width
        self.height = height
        self.entry_pos = entry_pos
        self.exit_pos = exit_pos
        self.perfect = perfect
        # Own random generator: a global random.seed() could be changed
        # by the program that uses this class (Pac-Man).
        self.rng = random.Random(seed)
        self.walls: list[list[dict[str, bool]]] = []
        self.pattern_cells: set[tuple[int, int]] = set()
        self.pattern_placed = False

    def generate(self) -> None:
        """Build a new maze in self.walls.

        Raises:
            ValueError: entry or exit is outside the maze, on the "42",
                or both are the same cell, or (Pac-Man mode) the maze is
                too small to get 2 loops.
        """
        for attempt in range(MAX_TRIES):
            self._reset_walls()
            self._place_pattern()
            self._check_entry_exit()
            self._carve_dfs()
            if self.perfect:
                return
            self._remove_dead_ends()
            # Pac-Man needs at least 2 loops. On small mazes we can be
            # unlucky, so we try again with the next random numbers.
            if self._count_loops() >= 2:
                return
        raise ValueError("maze too small for a Pac-Man board with 2 loops")

    def _reset_walls(self) -> None:
        """Close the 4 walls of every cell."""
        self.walls = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # A new dict for each cell, so cells never share walls.
                row.append({"N": True, "E": True, "S": True, "W": True})
            self.walls.append(row)

    def _place_pattern(self) -> None:
        """Find the cells of the "42", centred in the maze.

        The pattern needs one free cell around it, so the maze must be at
        least 9x7. If it is smaller, pattern_placed stays False.
        """
        self.pattern_cells = set()
        self.pattern_placed = False
        if self.width < 9 or self.height < 7:
            return
        left = self.width // 2 - 3
        top = self.height // 2 - 2
        for row in range(len(PATTERN_42)):
            for column in range(len(PATTERN_42[row])):
                if PATTERN_42[row][column] == "#":
                    self.pattern_cells.add((left + column, top + row))
        self.pattern_placed = True

    def _check_entry_exit(self) -> None:
        """Raise ValueError if entry or exit can't be used.

        The config parser checks this too, but Pac-Man won't use it.
        """
        self._check_cell("entry", self.entry_pos)
        self._check_cell("exit", self.exit_pos)
        if self.entry_pos == self.exit_pos:
            raise ValueError("entry and exit must be different")

    def _check_cell(self, name: str, pos: tuple[int, int]) -> None:
        """Raise ValueError if pos is outside the maze or on the "42".

        Args:
            name: "entry" or "exit", only used in the error message.
            pos: the coordinates (x, y) to check.
        """
        x = pos[0]
        y = pos[1]
        if not self._is_inside(x, y):
            raise ValueError(f"{name} ({x},{y}) is outside the maze")
        if pos in self.pattern_cells:
            raise ValueError(f"{name} ({x},{y}) is on the 42 pattern")

    def _is_inside(self, x: int, y: int) -> bool:
        """Return True if (x, y) is a cell of the maze."""
        if x < 0 or x >= self.width:
            return False
        if y < 0 or y >= self.height:
            return False
        return True

    def _open_wall(self, x: int, y: int, direction: str) -> None:
        """Open a wall on both sides: the only place that changes walls.

        Args:
            x: column of the cell.
            y: row of the cell.
            direction: "N", "E", "S" or "W".
        """
        move = DIRECTIONS[direction]
        next_x = x + move[0]
        next_y = y + move[1]
        self.walls[y][x][direction] = False
        self.walls[next_y][next_x][OPPOSITE[direction]] = False

    def _close_wall(self, x: int, y: int, direction: str) -> None:
        """Close a wall on both sides (used to undo a bad _open_wall).

        Args:
            x: column of the cell.
            y: row of the cell.
            direction: "N", "E", "S" or "W".
        """
        move = DIRECTIONS[direction]
        next_x = x + move[0]
        next_y = y + move[1]
        self.walls[y][x][direction] = True
        self.walls[next_y][next_x][OPPOSITE[direction]] = True

    def _carve_dfs(self) -> None:
        """Open walls with an iterative depth-first search from the entry.

        The stack holds the path walked so far. At each step we go to a
        random unvisited neighbour, or step back when there is none.
        """
        visited = set()
        # The "42" cells count as visited: the DFS never opens them.
        for cell in self.pattern_cells:
            visited.add(cell)
        visited.add(self.entry_pos)
        stack = [self.entry_pos]

        while len(stack) > 0:
            # The cell where we are now is the last one of the stack.
            current = stack[len(stack) - 1]
            x = current[0]
            y = current[1]

            # Directions that lead to a cell we have not visited yet.
            choices = []
            for direction in DIRECTIONS:
                move = DIRECTIONS[direction]
                next_x = x + move[0]
                next_y = y + move[1]
                if self._is_inside(next_x, next_y):
                    if (next_x, next_y) not in visited:
                        choices.append(direction)

            if len(choices) == 0:
                # Dead end: go back one cell.
                stack.pop()
            else:
                direction = self.rng.choice(choices)
                move = DIRECTIONS[direction]
                next_cell = (x + move[0], y + move[1])
                self._open_wall(x, y, direction)
                visited.add(next_cell)
                stack.append(next_cell)

    def _count_openings(self, x: int, y: int) -> int:
        """Return how many walls of the cell (x, y) are open."""
        count = 0
        for direction in DIRECTIONS:
            if not self.walls[y][x][direction]:
                count = count + 1
        return count

    def _count_loops(self) -> int:
        """Return how many independent loops the maze has.

        A maze with n cells and no loop has exactly n - 1 open walls
        (that is what the DFS makes). Each extra open wall adds one loop.
        """
        cells = 0
        open_walls = 0
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.pattern_cells:
                    continue
                cells = cells + 1
                # Only east and south, so each open wall is counted once.
                if not self.walls[y][x]["E"]:
                    open_walls = open_walls + 1
                if not self.walls[y][x]["S"]:
                    open_walls = open_walls + 1
        return open_walls - (cells - 1)

    def _is_dead_end(self, x: int, y: int) -> bool:
        """Return True if (x, y) is a corridor cell with only one opening."""
        if (x, y) in self.pattern_cells:
            return False
        return self._count_openings(x, y) == 1

    def _is_open_3x3(self, left: int, top: int) -> bool:
        """Return True if the 3x3 square at (left, top) has no inner wall.

        A 3x3 square has 12 inner walls: 6 east walls and 6 south walls.
        """
        for row in range(3):
            for column in range(3):
                x = left + column
                y = top + row
                if column < 2 and self.walls[y][x]["E"]:
                    return False
                if row < 2 and self.walls[y][x]["S"]:
                    return False
        return True

    def _creates_open_3x3(self, x: int, y: int) -> bool:
        """Return True if a 3x3 square around (x, y) is fully open.

        We test every 3x3 square that contains (x, y) and fits in the maze.
        """
        for top in range(y - 2, y + 1):
            for left in range(x - 2, x + 1):
                # The square goes from (left, top) to (left + 2, top + 2).
                fits = (self._is_inside(left, top)
                        and self._is_inside(left + 2, top + 2))
                if fits and self._is_open_3x3(left, top):
                    return True
        return False

    def _can_open(self, x: int, y: int, direction: str) -> bool:
        """Return True if the wall can be opened to make a loop.

        The wall must be closed, and lead to a cell inside the maze that
        is not part of the "42".
        """
        if not self.walls[y][x][direction]:
            return False
        move = DIRECTIONS[direction]
        next_x = x + move[0]
        next_y = y + move[1]
        if not self._is_inside(next_x, next_y):
            return False
        if (next_x, next_y) in self.pattern_cells:
            return False
        return True

    def _walls_to_try(self, x: int, y: int) -> list[str]:
        """Return the walls of a dead end we can open, best ones first.

        A wall toward another dead end is best: opening it removes two
        dead ends at once.
        """
        best = []
        others = []
        for direction in DIRECTIONS:
            if self._can_open(x, y, direction):
                move = DIRECTIONS[direction]
                if self._is_dead_end(x + move[0], y + move[1]):
                    best.append(direction)
                else:
                    others.append(direction)
        self.rng.shuffle(best)
        self.rng.shuffle(others)
        return best + others

    def _try_open(self, x: int, y: int, direction: str) -> bool:
        """Open the wall, unless it makes a 3x3 open area.

        Returns:
            True if the wall stays open, False if it was closed again.
        """
        move = DIRECTIONS[direction]
        next_x = x + move[0]
        next_y = y + move[1]
        self._open_wall(x, y, direction)
        if self._creates_open_3x3(x, y):
            self._close_wall(x, y, direction)
            return False
        if self._creates_open_3x3(next_x, next_y):
            self._close_wall(x, y, direction)
            return False
        return True

    def _remove_dead_ends(self) -> None:
        """Open one more wall at each dead end, to make loops (Pac-Man).

        Cells are taken in a random order, so the loops are spread over
        the whole maze.
        """
        cells = []
        for y in range(self.height):
            for x in range(self.width):
                cells.append((x, y))
        self.rng.shuffle(cells)

        for cell in cells:
            x = cell[0]
            y = cell[1]
            if self._is_dead_end(x, y):
                for direction in self._walls_to_try(x, y):
                    if self._try_open(x, y, direction):
                        break

    def solve(self, start: tuple[int, int], end: tuple[int, int]) -> str:
        """Return the shortest path from start to end, like "EESWN".

        Breadth-first search: cells are visited in order of distance from
        start, so the first time we reach end, the path is the shortest.

        Args:
            start: first cell (x, y).
            end: last cell (x, y).

        Returns:
            One letter per step, or "" if end can't be reached.
        """
        # For each cell we reach, remember the cell we came from
        # and the letter of the step, to rebuild the path at the end.
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        step_letter: dict[tuple[int, int], str] = {}
        seen = set()
        seen.add(start)
        queue: deque[tuple[int, int]] = deque()
        queue.append(start)

        while len(queue) > 0:
            current = queue.popleft()
            if current == end:
                break
            x = current[0]
            y = current[1]
            for direction in DIRECTIONS:
                wall_is_open = not self.walls[y][x][direction]
                move = DIRECTIONS[direction]
                neighbour = (x + move[0], y + move[1])
                if wall_is_open and neighbour not in seen:
                    seen.add(neighbour)
                    came_from[neighbour] = current
                    step_letter[neighbour] = direction
                    queue.append(neighbour)

        if end not in seen:
            return ""

        # Walk back from end to start, then put the letters in order.
        letters = []
        cell = end
        while cell != start:
            letters.append(step_letter[cell])
            cell = came_from[cell]
        letters.reverse()
        return "".join(letters)
