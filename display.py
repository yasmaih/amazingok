"""Draw the maze in the terminal with colors, and run the menu."""

from mazegen import MazeGenerator
from mazegen.generator import DIRECTIONS
from output_writer import write_output

# ANSI codes: "\033[...m" changes the text color, RESET goes back to normal.
RESET = "\033[0m"
CLEAR_SCREEN = "\033[2J\033[H"
COLORS = {
    "white": "\033[97m",
    "cyan": "\033[96m",
    "magenta": "\033[95m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "green": "\033[92m",
    "red": "\033[91m",
}
COLOR_NAMES = ["white", "cyan", "magenta", "yellow", "blue"]
BLOCK = "██"

# One letter per kind of square in the character grid.
WALL = "#"
EMPTY = " "
PATTERN = "4"
PATH = "."
ENTRY = "E"
EXIT = "X"


def build_char_grid(gen: MazeGenerator, path_letters: str,
                    show_path: bool) -> list[list[str]]:
    """Turn the walls into a grid of squares, ready to draw.

    The grid is (2 * height + 1) x (2 * width + 1): the cell (x, y) is at
    grid[2 * y + 1][2 * x + 1], and the squares between cells are walls
    or open passages.

    Args:
        gen: a generator on which generate() was called.
        path_letters: shortest path from entry to exit, like "EESWN".
        show_path: True to mark the path on the grid.

    Returns:
        A list of rows, each row a list of one-letter strings.
    """
    grid = []
    for row in range(2 * gen.height + 1):
        line = []
        for column in range(2 * gen.width + 1):
            line.append(WALL)
        grid.append(line)

    for y in range(gen.height):
        for x in range(gen.width):
            grid_x = 2 * x + 1
            grid_y = 2 * y + 1
            if (x, y) in gen.pattern_cells:
                grid[grid_y][grid_x] = PATTERN
            else:
                grid[grid_y][grid_x] = EMPTY
            # Only east and south: the west and north walls are the east
            # and south walls of the neighbours, already drawn.
            if not gen.walls[y][x]["E"]:
                grid[grid_y][grid_x + 1] = EMPTY
            if not gen.walls[y][x]["S"]:
                grid[grid_y + 1][grid_x] = EMPTY

    if show_path:
        # Follow the letters from the entry. In the grid, one step is two
        # squares: first the open passage, then the next cell.
        grid_x = 2 * gen.entry_pos[0] + 1
        grid_y = 2 * gen.entry_pos[1] + 1
        for letter in path_letters:
            move = DIRECTIONS[letter]
            for square in range(2):
                grid_x = grid_x + move[0]
                grid_y = grid_y + move[1]
                grid[grid_y][grid_x] = PATH

    grid[2 * gen.entry_pos[1] + 1][2 * gen.entry_pos[0] + 1] = ENTRY
    grid[2 * gen.exit_pos[1] + 1][2 * gen.exit_pos[0] + 1] = EXIT
    return grid


def render(grid: list[list[str]], wall_color: str,
           pattern_color: str) -> str:
    """Turn the grid into one colored string, 2 characters per square.

    Args:
        grid: the grid from build_char_grid().
        wall_color: a name from COLORS, for the walls.
        pattern_color: a name from COLORS, for the "42".

    Returns:
        The text to print.
    """
    # What to print for each kind of square.
    square_text = {
        WALL: COLORS[wall_color] + BLOCK + RESET,
        EMPTY: "  ",
        PATTERN: COLORS[pattern_color] + BLOCK + RESET,
        PATH: COLORS["yellow"] + "··" + RESET,
        ENTRY: COLORS["green"] + BLOCK + RESET,
        EXIT: COLORS["red"] + BLOCK + RESET,
    }
    lines = []
    for row in grid:
        line = ""
        for square in row:
            line = line + square_text[square]
        lines.append(line)
    return "\n".join(lines)


def next_color(current: str) -> str:
    """Return the color that comes after current in COLOR_NAMES.

    After the last color, we start again from the first one.
    """
    index = COLOR_NAMES.index(current) + 1
    if index == len(COLOR_NAMES):
        index = 0
    return COLOR_NAMES[index]


def run_menu(gen: MazeGenerator, output_file: str, show_path: bool) -> None:
    """Show the maze and a menu until the user quits.

    Args:
        gen: a generator on which generate() was called.
        output_file: file rewritten when a new maze is generated.
        show_path: True to show the shortest path at the start.

    Raises:
        OSError: the output file can't be rewritten.
    """
    wall_color = "white"
    pattern_color = "cyan"
    path_letters = gen.solve(gen.entry_pos, gen.exit_pos)
    message = ""
    while True:
        grid = build_char_grid(gen, path_letters, show_path)
        print(CLEAR_SCREEN + render(grid, wall_color, pattern_color))
        if not gen.pattern_placed:
            print("Error: maze too small for the 42 pattern (needs 9x7)")
        print(message)
        print("1: new maze   2: show/hide path   3: wall color   "
              "4: 42 color   5: quit")
        try:
            choice = input("Choice: ").strip()
        except EOFError:
            # Ctrl-D: no more input.
            print()
            return
        except KeyboardInterrupt:
            # Ctrl-C.
            print()
            return
        message = ""
        if choice == "1":
            gen.generate()
            path_letters = gen.solve(gen.entry_pos, gen.exit_pos)
            write_output(output_file, gen, path_letters)
            message = f"New maze written to {output_file}"
        elif choice == "2":
            show_path = not show_path
        elif choice == "3":
            wall_color = next_color(wall_color)
        elif choice == "4":
            pattern_color = next_color(pattern_color)
        elif choice == "5":
            return
        else:
            message = f"Unknown choice '{choice}': type a number from 1 to 5"
