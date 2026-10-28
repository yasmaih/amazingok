"""A-Maze-ing: read a config, generate a maze, write it and show it."""

import sys

from config_parser import ConfigError, load_config
from display import run_menu
from mazegen import MazeGenerator
from output_writer import write_output


def main() -> int:
    """Run the program. Return the exit code: 0 if ok, 1 on error."""
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        return 1
    try:
        config = load_config(sys.argv[1])
        gen = MazeGenerator(config.width, config.height, config.entry_pos,
                            config.exit_pos, config.perfect, config.seed)
        gen.generate()
        path_letters = gen.solve(config.entry_pos, config.exit_pos)
        write_output(config.output_file, gen, path_letters)
        # The menu also prints the "42 omitted" error when needed.
        run_menu(gen, config.output_file, config.show_path)
    except ConfigError as error:
        print(f"Error: {error}")
        return 1
    except ValueError as error:
        print(f"Error: {error}")
        return 1
    except OSError as error:
        print(f"Error: cannot write the output file: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
