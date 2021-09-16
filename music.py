import re
import discord
from discord.ext import commands
import asyncio

import youtube_dl

class MusicBot(commands.Cog):

    pode_ser_alguem = {
        "pode_ser_funk": {
            "keys": [
                "KondZilla",
                "mc",
                "funk"
            ],
            "frase": "Mds cara, isso parece funk. Cê escuta isso? Enfim..."
        },
        "eh_o_matheus_emo": {
            "keys": [
                "fresno",
                "triste",
                "sofre",
                "nxzero",
                "nx zero"
            ],
            "frase": "Será que ta tudo bem com o Matheus? Deve ta chorando, tadinho :("
        }
    }


    def __init__(self, bot, genius):
        self.bot = bot
        self.genius = genius

        self.is_playing = False

        #[song, channel]
        self.music_queue = []
        # for i in range(64):
        #     example = {}
        #     example["title"] = f"musica de numero {i+1}"
        #     self.music_queue.append([example, ""])

        self.now_playing = ""
        self.YDL_OPTIONS = {
            'format': 'bestaudio/best',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
        }
        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn"
        }
        self.voice_channel = ""


    def find_url_youtube(self, url):
        with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % url, download=False)["entries"][0]
            except Exception:
                return False

            try:
                info_track = info["track"]
                info_artist = info["artist"]
            except Exception:
                info_track = ""
                info_artist = ""

        return {
            "source": info["formats"][0]["url"],
            "title": info["title"],
            "description": info["description"],
            "track": info_track.split("(Ao Vivo)")[0],
            "artist": info_artist.split("FEAT.")[0]
        }


    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            first_url = self.music_queue[0][0]["source"]
            self.now_playing = self.music_queue[0][0]
            
            self.music_queue.pop(0)

            #after: quando terminar de tocar, vai chamar novamente a funcao play_next
            self.voice_channel.play(discord.FFmpegPCMAudio(first_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False


    async def play_music(self, music_n):
        if len(self.music_queue) > 0:
            self.is_playing = True

            first_url = self.music_queue[music_n][0]["source"]

            #tenta conectar ao canal se ainda nao tiver conectado
            if self.voice_channel == "" or not self.voice_channel.is_connected():
                self.voice_channel = await self.music_queue[music_n][1].connect()
            else:
                await self.voice_channel.move_to(self.music_queue[music_n][1])

            self.now_playing = self.music_queue[0][0]
            
            self.music_queue.pop(music_n)
            
            #after: quando terminar de tocar, vai chamar novamente a funcao play_next
            self.voice_channel.play(discord.FFmpegPCMAudio(first_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False


    @commands.command()
    async def help(self, context):
        embed = discord.Embed(
            title="Como usar essa bagaça",
            description="Comandos atualmente funcionais:",
            colour=context.author.colour,
        )

        embed.add_field(name='!help', value='Isso aqui que cê ta vendo')
        embed.add_field(name='!p <nome da musica>', value='Escutar a musiquinha que vc quer. Por enquanto não funfa playlist :(')
        embed.add_field(name='!q', value='Mostra as músicas que estão em espera na fila')
        embed.add_field(name='!skip', value='Pula pra próxima música')
        embed.add_field(name='!skipto <numero>', value='Pula pra música desejada')
        embed.add_field(name='!pause', value='Pausa a música atual (a próxima que não é, né)')
        embed.add_field(name='!resume', value='Retorna do pause (me obrigaram a não usar unpause)')
        embed.add_field(name='!dc', value='Chuta o bot do canal')
        embed.add_field(name='!lyrics', value='Mostra a letra da música atual (porcamente ainda)')
        embed.add_field(name='!lyrics <nome da musica#artista>', value='Mostra a letra da música desejada (porcamente ainda)')
        embed.add_field(name='!clear', value='Limpa a lista de músicas')
        embed.add_field(name='!remove <musica>', value='Remove a música (passa o índice, não o nome, porfa')
    
        await context.send(embed=embed)


    @commands.command()
    async def p(self, context, *args):
        query = " ".join(args)

        #salva o canal que o usuario esta
        try:
            voice_channel = context.author.voice.channel
        except AttributeError:
            await context.send("Você precisa ta num canal, lerdão. Vai escutar como?")
        else:
            song = self.find_url_youtube(query)
            if type(song) == type(True):
                await context.send("Nao consegui achá :O.")
            else:
                for key, value in self.pode_ser_alguem.items():
                    for key_wrod in value["keys"]:
                        substr = re.escape(key_wrod)
                        if re.compile(fr'\b{substr}\b', flags=re.I).findall(song["description"]):
                            await context.send(value["frase"])
                            break

                await context.send("%s adicionada a fila" % song["title"])
                self.music_queue.append([song, voice_channel])

                if not self.is_playing:
                    await self.play_music(0)

    
    @commands.command()
    async def q(self, context):
        retval = "```"
        all_music_pages = []
        for i in range(0, len(self.music_queue)):
            retval += f"{i + 1} - {self.music_queue[i][0]['title']} \n"

            if (i+1) % 10 == 0 and i != 0:
                retval += "```"
                all_music_pages.append(retval)

                retval = "```"

        retval += "```"
        if "``````" in retval:
            retval = ""
        if retval != "":
            all_music_pages.append(retval)
        elif retval == "" and len(all_music_pages) == 0:
            await context.send("Tem nada aqui irmão")
            return

        pages = len(all_music_pages)
        cur_page = 1
        prev_page = cur_page
        message = await context.send(f"Página {cur_page}/{pages}:\n{all_music_pages[cur_page-1]}")
        
        #getting the message object for editing and reacting
        await message.add_reaction("⏮")
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        await message.add_reaction("⏭")
        

        def check(reaction, user):
            #this makes sure nobody except the command sender can interact with the "menu"
            return user == context.author and str(reaction.emoji) in ["◀️", "▶️", "⏮", "⏭"]

        while True:
            try:
                prev_page = cur_page
                # waiting for a reaction to be added - times out after 20 seconds
                reaction, user = await self.bot.wait_for("reaction_add", timeout=20, check=check)

                if str(reaction.emoji) == "▶️" and cur_page != pages:
                    cur_page += 1
                elif str(reaction.emoji) == "⏭" and cur_page != pages:
                    cur_page = pages
                elif str(reaction.emoji) == "◀️" and cur_page > 1:
                    cur_page -= 1
                elif str(reaction.emoji) == "⏮" and cur_page > 1:
                    cur_page = 1
                else:
                    #removes reactions if the user tries to go forward on the last page or
                    #backwards on the first page
                    await message.remove_reaction(reaction, user)

                if prev_page != cur_page:
                    await message.edit(content=f"Página {cur_page}/{pages}:\n{all_music_pages[cur_page-1]}")
                    await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                await message.delete()
                #ending the loop if user doesn't react after x seconds
                break

    
    @commands.command()
    async def skip(self, context):
        if self.voice_channel != "":
            if len(self.music_queue) >= 0:
                self.voice_channel.stop()
                await self.play_music(0)
            else:
                await context.send("Tem música o suficiente pra isso não. Da um queue antes aí.")

    
    @commands.command()
    async def skipto(self, context, *args):
        music_n = " ".join(args)
        if self.voice_channel != "":
            if len(self.music_queue) >= int(music_n):
                self.voice_channel.stop()
                await self.play_music(int(music_n) - 1)
            else:
                await context.send("Tem música o suficiente pra isso não. Da um queue antes aí.")

    
    @commands.command()
    async def pause(self, context):
        if self.is_playing:
            self.voice_channel.pause()
            self.is_playing = False


    @commands.command()
    async def resume(self, context):
        if not self.is_playing:
            self.voice_channel.resume()
            self.is_playing = True
    

    @commands.command()
    async def dc(self, context):
        if context.author.voice is None:
            await context.send("Cê nem ta no canal. Quer expulsar o bot pq, cusão?")
            return

        if self.voice_channel != "":
            await context.send("Toino lá. Vlw Flws :3")
            await context.voice_client.disconnect()


    @commands.command()
    async def lyrics(self, context, *args):
        music_info = ":".join(args).replace(":", " ").split("#")

        if len(music_info) == 2:
            music_name = music_info[0]
            music_artist = music_info[1]
        elif len(music_info) != 2 and len(music_info) != 1:
            await context.send("Para uma música específica, deve ser pesquisada como: ```nome da musica#artista```")
            return
        elif len(music_info) == 1:
            if self.is_playing:
                music_name = self.now_playing["track"]
                music_artist = self.now_playing["artist"]
            else:   
                await context.send("Não ta tocando nada. Para uma música específica, deve ser pesquisada como: ```nome da musica#artista```")
                return

        async with context.typing():
            song = self.genius.search_song(music_name, music_artist).lyrics

        embed = discord.Embed(
            title=music_name,
            description=song,
            colour=context.author.colour,
        )

        #embed.set_thumbnail(url=song["thumbnail"]["genius"])
        embed.set_author(name=music_artist)
        await context.send(embed=embed)


    @commands.command()
    async def clear(self, context):
        self.music_queue = []

    
    @commands.command()
    async def remove(self, context, *args):
        music_n = int(" ".join(args))
        if context.author.voice is None:
            await context.send("Cê nem ta no canal. Quer excluir a música pq?")
            return

        if self.voice_channel != "":
            if len(self.music_queue) >= music_n:
                self.music_queue.pop(music_n - 1)