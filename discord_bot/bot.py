import argparse

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
    """
        Função principal que inicializa o bot e todas as suas funções

        param test_env: flag que indica se estamos em um ambiente de testes
    """

    initializer.Initializer(test_env)


if __name__ == '__main__':
    args = get_arguments()

    main(args.t)