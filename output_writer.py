"""Write the maze to a file, one hexadecimal digit per cell."""

from mazegen import MazeGenerator

# Value of each closed wall, from the subject: bit 0 = N, 1 = E, 2 = S, 3 = W.
WALL_VALUES = {"N": 1, "E": 2, "S": 4, "W": 8}
HEX_DIGITS = "0123456789ABCDEF"


def to_hex_rows(walls: list[list[dict[str, bool]]]) -> list[str]:
    """Turn the walls into one string of hex digits per row."""
    rows = []
    for row in walls:
        text = ""
        for cell in row:
            value = 0
            for direction in WALL_VALUES:
                if cell[direction]:
                    value = value + WALL_VALUES[direction]
            text = text + HEX_DIGITS[value]
        rows.append(text)
    return rows


def write_output(path: str, gen: MazeGenerator, path_letters: str) -> None:
    """Write the hex rows, an empty line, entry, exit and the path."""
    entry = gen.entry_pos
    exit_pos = gen.exit_pos
    with open(path, "w") as file:
        for row in to_hex_rows(gen.walls):
            file.write(row + "\n")
        file.write("\n")
        file.write(f"{entry[0]},{entry[1]}\n")
        file.write(f"{exit_pos[0]},{exit_pos[1]}\n")
        file.write(path_letters + "\n")
