"""Read the config file and turn it into a MazeConfig."""

import os
from dataclasses import dataclass

REQUIRED_KEYS = [
    "WIDTH",
    "HEIGHT",
    "ENTRY",
    "EXIT",
    "OUTPUT_FILE",
    "PERFECT",
]

OPTIONAL_KEYS = {
    "SEED": "",
    "SHOW_PATH": "False",
}

MAX_SIZE = 100


class ConfigError(Exception):
    """Raised when the config file is missing or has a bad line or value."""


@dataclass
class MazeConfig:
    """The settings of the config file, converted to the right types.

    For example WIDTH=20 in the file gives config.width == 20.
    """

    width: int
    height: int
    entry_pos: tuple[int, int]
    exit_pos: tuple[int, int]
    output_file: str
    perfect: bool
    seed: int | None
    show_path: bool


def parse_int(key: str, value: str) -> int:
    """Turn a value like "20" into the number 20.

    Args:
        key: name of the key, only used in the error message.
        value: what is written after the = in the file.

    Returns:
        The number.
    """
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"{key}: '{value}' is not a number")


def parse_bool(key: str, value: str) -> bool:
    """Turn "True" or "False" into a bool. "true" and "TRUE" work too.

    Args:
        key: name of the key, only used in the error message.
        value: what is written after the = in the file.

    Returns:
        True or False.
    """
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    raise ConfigError(f"{key}: '{value}' must be True or False")


def parse_coords(key: str, value: str) -> tuple[int, int]:
    """Turn a value like "19,14" into the tuple (19, 14).

    Args:
        key: name of the key, only used in the error message.
        value: what is written after the = in the file.

    Returns:
        The coordinates (x, y).
    """
    numbers = value.split(",")
    if len(numbers) != 2:
        raise ConfigError(f"{key}: '{value}' must be written x,y")
    x = parse_int(key, numbers[0].strip())
    y = parse_int(key, numbers[1].strip())
    return (x, y)


def check_inside(key: str, pos: tuple[int, int], width: int,
                 height: int) -> None:
    """Raise a ConfigError if pos is outside the maze.

    Negative values must be refused here: in Python walls[0][-1] does
    not crash, it reads the last column.

    Args:
        key: name of the key, only used in the error message.
        pos: the coordinates (x, y) to check.
        width: width of the maze.
        height: height of the maze.
    """
    x = pos[0]
    y = pos[1]
    if x < 0 or x >= width or y < 0 or y >= height:
        raise ConfigError(
            f"{key}: ({x},{y}) is outside the {width}x{height} maze")


def read_raw_values(path: str) -> dict[str, str]:
    """Read the file and keep each KEY=VALUE line as text.

    Empty lines and lines starting with # are skipped. A line without =,
    an unknown key or a key written twice raises a ConfigError.

    """
    try:
        # utf-8-sig also reads files saved by Windows Notepad
        with open(path, encoding="utf-8-sig") as file:
            lines = file.readlines()
    except OSError:
        raise ConfigError(f"cannot open '{path}'")
    except UnicodeDecodeError:
        raise ConfigError(f"'{path}' is not a text file")

    raw_values: dict[str, str] = {}
    line_number = 0
    for line in lines:
        line_number = line_number + 1
        clean_line = line.strip()
        if clean_line == "" or clean_line.startswith("#"):
            continue
        if "=" not in clean_line:
            raise ConfigError(f"line {line_number}: no '=' in '{clean_line}'")
        key_and_value = clean_line.split("=", 1)
        key = key_and_value[0].strip()
        value = key_and_value[1].strip()
        if key not in REQUIRED_KEYS and key not in OPTIONAL_KEYS:
            raise ConfigError(f"line {line_number}: unknown key '{key}'")
        if key in raw_values:
            raise ConfigError(f"line {line_number}: '{key}' is written twice")
        raw_values[key] = value
    return raw_values


def load_config(config_path: str) -> MazeConfig:
    """Read the config file, check every value and return a MazeConfig.

    ENTRY and EXIT are checked here, and the generator checks them again,
    because Pac-Man will use the generator without a config file.

    """
    raw_values = read_raw_values(config_path)

    for key in REQUIRED_KEYS:
        if key not in raw_values:
            raise ConfigError(f"the key '{key}' is missing")
    for key in OPTIONAL_KEYS:
        if key not in raw_values:
            raw_values[key] = OPTIONAL_KEYS[key]

    width = parse_int("WIDTH", raw_values["WIDTH"])
    height = parse_int("HEIGHT", raw_values["HEIGHT"])
    if width < 2 or height < 2:
        raise ConfigError("WIDTH and HEIGHT must be at least 2")
    if width > MAX_SIZE or height > MAX_SIZE:
        raise ConfigError(f"WIDTH and HEIGHT must be at most {MAX_SIZE}")

    entry_pos = parse_coords("ENTRY", raw_values["ENTRY"])
    exit_pos = parse_coords("EXIT", raw_values["EXIT"])
    check_inside("ENTRY", entry_pos, width, height)
    check_inside("EXIT", exit_pos, width, height)
    if entry_pos == exit_pos:
        raise ConfigError("ENTRY and EXIT must be different")

    output_file = raw_values["OUTPUT_FILE"]
    if output_file == "":
        raise ConfigError("OUTPUT_FILE is empty")
    if os.path.abspath(output_file) == os.path.abspath(config_path):
        raise ConfigError("OUTPUT_FILE can't be the config file itself")

    perfect = parse_bool("PERFECT", raw_values["PERFECT"])
    show_path = parse_bool("SHOW_PATH", raw_values["SHOW_PATH"])

    seed = None
    if raw_values["SEED"] != "":
        seed = parse_int("SEED", raw_values["SEED"])

    return MazeConfig(
        width=width,
        height=height,
        entry_pos=entry_pos,
        exit_pos=exit_pos,
        output_file=output_file,
        perfect=perfect,
        seed=seed,
        show_path=show_path,
    )
