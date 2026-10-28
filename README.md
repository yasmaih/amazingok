*This activity has been created as part of the 42 curriculum by yaichi and nturcot.*

# A-Maze-ing

## Description

A-Maze-ing reads a config file, generates a maze, writes it to a file in
hexadecimal, and shows it in the terminal with a small interactive menu.
The generator lives in the `mazegen` package, so a later project (Pac-Man)
can install it as a `.whl` and reuse it.

## Instructions

```sh
make install    # create .venv and install flake8, mypy, build
make run        # python3 a_maze_ing.py config.txt
make debug      # same, inside the pdb debugger
make lint       # flake8 + mypy
make build      # build mazegen-1.0.0-py3-none-any.whl at the root
make clean      # remove caches and build files
```

## Config file

One `KEY=VALUE` per line. Empty lines and lines starting with `#` are
ignored. Spaces around the key and the value are removed.

| Key | Required | Format | Example |
|---|---|---|---|
| `WIDTH` | yes | integer, 2 to 100 | `WIDTH=20` |
| `HEIGHT` | yes | integer, 2 to 100 | `HEIGHT=15` |
| `ENTRY` | yes | `x,y` inside the maze | `ENTRY=0,0` |
| `EXIT` | yes | `x,y` inside the maze, not equal to `ENTRY` | `EXIT=19,14` |
| `OUTPUT_FILE` | yes | file name, not the config file itself | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | yes | `True` or `False` (any case) | `PERFECT=False` |
| `SEED` | no | integer; missing or empty = new maze every run | `SEED=42` |
| `SHOW_PATH` | no | `True` or `False`, default `False` | `SHOW_PATH=False` |

`x` is the column and `y` is the row, both start at 0. The "42" pattern
needs `WIDTH >= 9` and `HEIGHT >= 7`.

An unknown key, a key written twice, a missing key or a bad value stops the
program with a clear `Error: ...` message (with the line number when
possible).

## Display and menu

The maze is drawn in the terminal with `██` blocks and ANSI colors: walls,
the "42" pattern, the entry (green), the exit (red) and the shortest path
(yellow dots). The menu:

| Key | Action |
|---|---|
| `1` | generate a new maze and rewrite the output file |
| `2` | show / hide the shortest path |
| `3` | change the wall color |
| `4` | change the "42" color |
| `5` | quit (Ctrl-D and Ctrl-C quit too) |

## Output file

One hexadecimal digit per cell, one line per row. Each closed wall adds
its value: North 1, East 2, South 4, West 8 (so `F` = all 4 walls closed).
Then an empty line, the entry `x,y`, the exit `x,y`, and the shortest path
with the letters `N`, `E`, `S`, `W`.

## Maze generation algorithm

Iterative depth-first search ("recursive backtracker" written with a stack):

1. Every cell starts with its 4 walls closed.
2. Push the entry on a stack and mark it visited.
3. Look at the cell on top of the stack. If it has unvisited neighbours,
   pick one at random, open the wall between them, mark it visited and push
   it. Otherwise pop the cell (step back).
4. Stop when the stack is empty: every cell has been visited.

Each new cell is reached by opening exactly one wall, so a maze of `n`
cells has `n - 1` open walls: it is connected and has no loop (a perfect
maze).

**Why this algorithm:** it is short, gives long winding corridors, and
needs only a list as a stack. It is written with a loop instead of
recursion because Python stops at about 1000 nested calls, and a 100x100
maze can go 10 000 cells deep. The random choices come from
`random.Random(seed)`, an object owned by the generator, so the same seed
always gives the same maze.

**The "42":** 20 cells in the middle stay fully closed. They are marked
as visited before the DFS starts, so the DFS never opens them. The pattern
needs a 9x7 maze; smaller mazes are drawn without it and an error is
printed.

**`PERFECT=False` (Pac-Man board, the default):** the perfect maze is made
first. Then every dead end opens one more wall, preferably toward another
dead end, which creates loops. A wall that would make a 3x3 open area is
closed again, because corridors can't be wider than 2 cells. Result:
fully connected, corners and centre reachable, many loops. The only dead
ends left are the small pockets inside the "42" drawing.
The board must have at least 2 loops: on a small maze the generator tries
again (up to 20 times), and a 2x2 maze raises a `ValueError`, because it
can only ever have one loop.

**Shortest path:** breadth-first search (BFS) from the entry. BFS reaches
cells in order of distance, so the first path that reaches the exit is a
shortest one.

## Reusable code

The `mazegen` package (`mazegen/generator.py`) is the reusable part. It
never prints, never reads a file and imports nothing from this project, so
another program (the Pac-Man project) can use it alone.

Build and install:

```sh
make install                                  # tools in .venv
make build                                    # mazegen-1.0.0-py3-none-any.whl
pip install mazegen-1.0.0-py3-none-any.whl    # in the other project
```

Use:

```python
from mazegen import MazeGenerator

gen = MazeGenerator(width=20, height=15, entry_pos=(0, 0),
                    exit_pos=(19, 14), perfect=False, seed=42)
gen.generate()                  # raises ValueError on a bad entry/exit

gen.walls[y][x]["N"]            # True if the north wall of (x, y) is closed
gen.pattern_cells               # set of the (x, y) cells of the "42"
gen.pattern_placed              # False if the maze was too small for it
gen.solve((0, 0), (19, 14))     # shortest path, like "EESSWN..."
```

- `width`, `height`: size in cells. `entry_pos`, `exit_pos`: `(x, y)`,
  `x` is the column.
- `perfect`: `True` for exactly one path, `False` (default) for a Pac-Man
  board with loops.
- `seed`: the same seed gives the same maze; `None` gives a new one.
- `generate()` can be called again to get a new maze.
- `solve(start, end)` works between any two cells (for example a ghost
  and the player).

## Project management

- **Team:** yaichi, an nturcot. 
- **Planned:** one week (2026-09-30 to 2026-10-07), one part per day:
  config parser, perfect generator, "42" + path + output file, Pac-Man
  mode, display, package + README, then a day to practice the defense.
- **How it evolved:** the setup and config parser were wrote by nturcot and the display.
- **What worked well:** writing the design first (data structures and
  algorithm choices decided before coding), small files with one job each,
  and checking every step with `maze_analyzer.py`, flake8 and mypy.
- **What could be improved:** closing each part (tests + lint + commit)
  before starting the next one, and keeping a margin day free.
- **Tools:** git, a Makefile, flake8, mypy, the provided
  `maze_analyzer.py`, small test scripts, Neovim, and Claude Code (see AI
  usage).

## Resources

- Makefile: <https://makefiletutorial.com/>

- Python `random`: <https://docs.python.org/3/library/random.html>
- Python `collections.deque`:
  <https://docs.python.org/3/library/collections.html#collections.deque>
- Maze generation algorithms (Jamis Buck):
  <https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap>
- Breadth-first search: <https://en.wikipedia.org/wiki/Breadth-first_search>
- ANSI escape codes: <https://en.wikipedia.org/wiki/ANSI_escape_code>
- Python packaging (pyproject.toml):
  <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>

### AI usage

Claude Code (Anthropic) was used as a tutor and pair programmer:

- **Design and planning:** discussing the options (DFS vs other
  algorithms, wall storage, display), then writing the design spec and the
  day-by-day plan.
- **Review:** reviewing the tooling (Makefile, flake8, pyproject.toml).
