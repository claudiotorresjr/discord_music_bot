import discord
from discord.ext import commands
import asyncio


class TicTacToeBot(commands.Cog):
    messages_tic = []
    tic_tac_toe = False
    tic_tac_toe_players = []
    tic_tac_toe_board = []


    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def veia(self, context, *args):
        self.tic_tac_toe_players.append(str(context.message.author).split("#")[0])

        if len(self.tic_tac_toe_players) == 1:
            await context.send("Esperando o outro jogador...")
        elif len(self.tic_tac_toe_players) == 2:
            embed = discord.Embed(
                title=f"Jogo da velha",
                description=f"{self.tic_tac_toe_players[0]} vs {self.tic_tac_toe_players[1]}",
                color=discord.Color.blurple(),
            )

            self.messages_tic = []
            self.tic_tac_toe = False
            self.tic_tac_toe_board = [":white_large_square:", ":white_large_square:", ":white_large_square:",
            ":white_large_square:", ":white_large_square:", ":white_large_square:",
            ":white_large_square:", ":white_large_square:", ":white_large_square:"]

            embed_message = await context.send(embed=embed)
            line = ""
            for i in range(len(self.tic_tac_toe_board)):
                if i == 2 or i == 5 or i == 8:
                    line += " " + self.tic_tac_toe_board[i]
                    self.messages_tic.append(await context.send(line))

                    line = ""
                else:
                    line += " " + self.tic_tac_toe_board[i]

            self.messages_tic.append(embed_message)

            #coloca as reações após as musicas
            await self.messages_tic[len(self.messages_tic)-2].add_reaction("↖️")
            await self.messages_tic[len(self.messages_tic)-2].add_reaction("⬆️")
            await self.messages_tic[len(self.messages_tic)-2].add_reaction("↗️")
            await self.messages_tic[len(self.messages_tic)-2].add_reaction("⬅️")
            await self.messages_tic[len(self.messages_tic)-2].add_reaction("🔵")
            await self.messages_tic[len(self.messages_tic)-2].add_reaction("➡️")
            await self.messages_tic[len(self.messages_tic)-2].add_reaction("↙️")
            await self.messages_tic[len(self.messages_tic)-2].add_reaction("⬇️")
            await self.messages_tic[len(self.messages_tic)-2].add_reaction("↘️")

            emojis = [
                "↖️", "⬆️", "↗️",
                "⬅️","🔵", "➡️",
                "↙️", "⬇️", "↘️"
            ]

            board = [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0]
            ]

            def check_endgame(board_line, board_col):
                #verifica as linhas horizontais
                if board[0][board_col] == board[1][board_col] == board[2][board_col]:
                    return True

                #verifica as linhas verticais
                if board[board_line][0] == board[board_line][1] == board[board_line][2]:
                    return True

                #verifica diagonal principal
                if (board_line == board_col) and (board[0][0] == board[1][1] == board[2][2]):
                    return True

                #verifica diagonal secundária
                if (board_line + board_col == 2) and (board[0][2] == board[1][1] == board[2][0]):
                    return True

                return False    

            def check(reaction, user):
                """
                Ter a certeza de que as reações que o bot colocou que serão processadas
                """ 

                return str(user).split("#")[0] in self.tic_tac_toe_players and str(reaction.emoji) in emojis

            total_reactions = 0
            while True:
                try:
                    #espera por 20 segundos (timeout) até receber alguma reação. apaga a mensagem se nao houver
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=20, check=check)
                    
                    pos = 1
                    mark = ":o2:"
                    if not self.tic_tac_toe:
                        mark = ":regional_indicator_x:"
                        pos = 2

                    emoji_index = emojis.index(str(reaction.emoji))

                    if self.tic_tac_toe_board[emoji_index] == ":white_large_square:":
                        self.tic_tac_toe_board[emoji_index] = mark
                        self.tic_tac_toe = not self.tic_tac_toe

                    line = ""
                    board_line = int(emoji_index / 3)
                    init = board_line * 3
                    end = init + 3
                    for i in range(init, end):
                        line += " " + self.tic_tac_toe_board[i]

                    board_col = emoji_index
                    if emoji_index >= 3 and emoji_index < 6:
                        board_col = emoji_index - 3
                    elif emoji_index >= 6:
                        board_col = emoji_index - 6

                    board[board_line][board_col] = pos
                    # print(board[0][0] , board[0][1], board[0][2])
                    # print(board[1][0] , board[1][1], board[1][2])
                    # print(board[2][0] , board[2][1], board[2][2])
                    # print("-"*15)

                    await self.messages_tic[board_line].edit(content=line)

                    if check_endgame(board_line, board_col):
                        embed = discord.Embed(
                            title=f"{str(user).split('#')[0]} venceu!! u.u",
                            color=discord.Color.blurple(),
                        )

                        embed_message = await context.send(embed=embed)
                        self.tic_tac_toe_players = []
                        self.messages_tic = []

                        break
                    
                    total_reactions += 1
                    if total_reactions == 9:
                        embed = discord.Embed(
                            title=f"Ninguém ganhô :(",
                            color=discord.Color.blurple(),
                        )

                        embed_message = await context.send(embed=embed)
                        self.tic_tac_toe_players = []
                        self.messages_tic = []

                        break


                except asyncio.TimeoutError:
                    for message in self.messages_tic:
                        await message.delete()
                    #acaba com o loop após o timeout
                    self.tic_tac_toe_players = []
                    self.messages_tic = []
                    break


    #@commands.command()
    #async def bota(self, context, *args):
    #    pass
        # pos = int(" ".join(args))

        # if not self.tic_tac_toe:
        #     mark = ":regional_indicator_x:"
        # else:
        #     mark = ":o2:"

        # self.tic_tac_toe = not self.tic_tac_toe
        # count = 0
        # if 0 < pos < 10 and self.board[pos - 1] == ":white_large_square:":
        #     self.board[pos - 1] = mark
        #     count += 1

        #     for message in self.messages_tic:
        #         await message.delete()

        #     self.messages_tic = []
        #     # print the self.board
        #     line = ""
        #     for x in range(len(self.board)):
        #         if x == 2 or x == 5 or x == 8:
        #             line += " " + self.board[x]
        #             self.messages_tic.append(await context.send(line))
        #             line = ""
        #         else:
        #             line += " " + self.board[x]


        #embed.description = "\n".join(messages)
        #await context.send(embed=embed)