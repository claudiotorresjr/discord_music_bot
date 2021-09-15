import re
import discord
from discord.ext import commands

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
        
        for i in range(0, len(self.music_queue)):
            retval += f"{i + 1} - {self.music_queue[i][0]['title']} \n"

        retval += "```"
        if "``````" in retval:
            retval = ""
        if retval != "":
            await context.send(retval)
        else:
            await context.send("Tem nada aqui irmão")

    
    @commands.command()
    async def skip(self, context):
        if self.voice_channel != "":
            self.voice_channel.stop()
            await self.play_music(0)

    
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
    async def stop(self, context):
        if context.author.voice is None:
            await context.send("Cê nem ta no canal. Quer expulsar o bot pq, cusão?")
            return

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