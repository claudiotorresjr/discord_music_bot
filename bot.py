from discord.ext import commands
import lyricsgenius as lg

import music

api_key = "KxJJBM-kYTWl3mQBB2LuPAU2WLDJyPqjL1IezfY3h7dke7s7v4F5N_3O4eV7AH66"
genius = lg.Genius(api_key)


my_bot = commands.Bot(command_prefix='!')
my_bot.add_cog(music.MusicBot(my_bot, genius))

TOKEN = "ODg3NTE4NDYyMzk2NzQzNzEy.YUFT-g.ESw2uCJIcFNw1HtiJ9OhKhgJXfE"

my_bot.run(TOKEN)