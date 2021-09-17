import argparse

from all_modules import musics
import initializer


def get_arguments():
    """
    Get command line arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t", help="Test env", action='store_true'
    )

    options = parser.parse_args()
    return options


def main(test_env):
    initializer.Initializer(test_env)


if __name__ == '__main__':
    args = get_arguments()

    main(args.t)