import discord
from discord.ext import commands
import lyricsgenius as lg
import argparse

import music


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
    genius_api_key = "KxJJBM-kYTWl3mQBB2LuPAU2WLDJyPqjL1IezfY3h7dke7s7v4F5N_3O4eV7AH66"
    genius = lg.Genius(genius_api_key)

    TOKEN = "ODg3NTE4NDYyMzk2NzQzNzEy.YUFT-g.ESw2uCJIcFNw1HtiJ9OhKhgJXfE"

    if test_env:
        prefix = "#"
        TOKEN = "ODg4MDU3ODcxNjg4OTQxNTk4.YUNKVw.a7CELQe1QMeI7-e3CcVwlYNtrXo"

    my_bot = commands.Bot(command_prefix=prefix, help_command=None)
    my_bot.add_cog(music.MusicBot(my_bot, genius))

    my_bot.run(TOKEN)


if __name__ == '__main__':
    args = get_arguments()

    main(args.t)