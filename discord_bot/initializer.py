import os
import pkgutil
import inspect
import importlib

from discord.ext import commands


class Initializer(object):
    def __init__(self, test_env):
        self.prefix = "!"
        self.TOKEN = "ODg3NTE4NDYyMzk2NzQzNzEy.YUFT-g.ESw2uCJIcFNw1HtiJ9OhKhgJXfE"

        if test_env:
            self.prefix = "#"
            self.TOKEN = "ODg4MDU3ODcxNjg4OTQxNTk4.YUNKVw.a7CELQe1QMeI7-e3CcVwlYNtrXo"

        self.my_bot = commands.Bot(command_prefix=self.prefix, help_command=None)

        for dir in os.listdir("discord_bot/all_modules"):
            self.import_modules_from_dir(f"all_modules.{dir}")

        self.my_bot.run(self.TOKEN)


    def import_modules_from_dir(self, dir_name):
        """
            Import all games modules inside all_games directory and instantiate it. 

        :   param string dir_name: directory to import modules from

        """

        module = importlib.import_module(dir_name)

        for _, modname, _ in pkgutil.iter_modules(module.__path__, f"{dir_name}."):
            imported_module = __import__(modname, fromlist="dummy")

            for name in dir(imported_module):
                cls = getattr(imported_module, name)
                if inspect.isclass(cls):
                    self.my_bot.add_cog(cls(self.my_bot))