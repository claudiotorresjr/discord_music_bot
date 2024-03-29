import re
import discord
from discord.ext import commands
import asyncio
import datetime
import time
import random

import psycopg2

import youtube_dl
import lyricsgenius as lg

import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse

from all_modules import musics
from database import database as db


class MusicBot(commands.Cog):
    """
        Classe base para os comandos relacionados ao bot de música
    """

    all_commands = [
        '-help',
        '-p',
        '-q',
        '-skip',
        '-skipto',
        '-pause',
        '-resume',
        '-dc',
        '-lyrics',
        '-clear'
        '-remove',
        '-np',
        '-gabi'
    ]

    gabi_oini = {
        "source": "https://musica-alexa-claudio.s3.sa-east-1.amazonaws.com/oni_converted.mp3",
        "title": "Gabi oini",
        "description": "",
        "track": "",
        "artist": "Gabi suprema",
        "requested_by": "O mundo",
        "thumbnail": "",
        "video_url": "",
        "video_duration": 4,
        "timestamp": datetime.datetime.utcnow(),
        "from_playlist": False
    }

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

    bot_request = False

    music_channel_id = 704020614314459176
    geral_channel_id = 259108205798359040

    rafa_id = 214169823620366338
    #samurai 420210840663359489

    def __init__(self, bot):
        """
            __init__
        """

        #cria o banco de dados.
        self.database = db.Database()
        self.database.connect()
        self.database.create_table()

        self.bot = bot

        self.is_playing = False
        self.music_atual_time = ""
        self.skiping = False
        self.music_queue = []
        self.save_music_queue = []

        self.np_is_running = False

        #aqui é pra testar a lista de músicas cheia :)
        # for i in range(64):
        #     example = {}
        #     example["title"] = f"musica de numero {i+1}"
        #     self.music_queue.append([example, ""])

        self.now_playing = ""
        self.voice_channel = ""
        self.voice_channel_id = ""
        self.music_stop_counter = False
        self.voice_source = ""

        self.genius_api_key = "KxJJBM-kYTWl3mQBB2LuPAU2WLDJyPqjL1IezfY3h7dke7s7v4F5N_3O4eV7AH66"
        self.genius = lg.Genius(self.genius_api_key)

        #configurações do modulo youtube_dl
        self.YDL_OPTIONS = {
            'writethumbnail': True,
            'format': 'bestaudio/best',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0', #ipv4 pois ipv6 causa erro as vezes
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192'
                },
                {'key': 'EmbedThumbnail'},
            ]
        }
        #configurações do ffmpeg (relacionadas ao áudio que será gerado)
        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn"
        }
        self.GOOGLE_API_KEY = "AIzaSyAiWvkOhhsUpXZX4xHg6vArSxGrSkN1OZM"
        self.youtube_url = "https://www.youtube.com/watch?v="

        self.who_is_in_voice = []

    def get_music_progress(self):
        if self.voice_source:
            return self.voice_source.music_progress
            #TODO: Properly implement this
            #       Correct calculation should be bytes_read/192k
            #       192k AKA sampleRate * (bitDepth / 8) * channelCount
            #       Change frame_count to bytes_read in the PatchedBuff

    @commands.Cog.listener()
    async def on_message(self, message):
        """
            É ativada sempre que alguma mensagem é enviada no servidor

            param message: mensagem enviada
        """

        if "Amonimiosu#8972" in str(message.author):
            split_msg = message.content.split(" ")
            command = split_msg[0]
            if command in self.all_commands:
                args = False
                if len(split_msg) > 1:
                    args = split_msg[1]
                ctx = await self.bot.get_context(message)

                self.bot_request = True
                if not args:
                    await ctx.invoke(self.bot.get_command(command.split('-')[1]))
                else:
                    await ctx.invoke(self.bot.get_command(command.split('-')[1]), args)

        #verifica se o bot foi marcado e manda uma resposta
        if self.bot.user.mentioned_in(message):
            await message.channel.send("Vo trabaiá hj não. Fica de boa aí")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        
        #verifica se um user (nao o bot) entrou/saiu no canal de voz
        if member.id != self.bot.user.id:
            #se o bot já estiver em um canal de voz, verifica se o usuario entrou ou saiu
            if self.voice_channel != "":
                #se o usuário entrou, member.voice nao é None.
                try:
                    #se o id do canal do usuario for igual ao do bot, entao estao no mesmo canal
                    if member.voice.channel.id == self.voice_channel_id:
                        #adiciona o id desse user na lista de pessoas no canal de voz
                        self.who_is_in_voice.append(member.id)

                        if member.id == self.rafa_id:
                            await self.bot.get_channel(self.music_channel_id).send("Ahh não. Chegou...")
                        #print(f"{member.name} entrou")
                #se foi exceptiom, member.voice é None. Então o user saiu do canal de voz
                except Exception:
                        #tenta remover o id do usuario da lista. é sucesso se o usuário estiver no mesmo
                        #canal de voz do bot.
                        try:
                            #remove o id desse user na lista de pessoas no canal de voz
                            self.who_is_in_voice.remove(member.id)
                            if member.id == self.rafa_id:
                                await self.bot.get_channel(self.music_channel_id).send("Graças a Deus a tortura acabou!")
                            #print(f"{member.name} saiu")
                        #a exception ocorre quando tenta tirar da lista e o id nao está la. Isso acontece se
                        #o usuário entrou em um outro canal diferente que o bot ta.
                        except Exception:
                            pass
            
        else:
            #verifica se o canal anterior é None. Então o bot chegou limpinho
            if before.channel is None:
                #print("Bot entrou no canal de voz")
                voice = after.channel.guild.voice_client

                #assim que o bot entra, pega todos que estão no canal de voz atual
                for user_id in voice.channel.voice_states.keys():
                    #se o rafa tiver no canal, o bot fica puto
                    if user_id == self.rafa_id:
                        await self.bot.get_channel(self.music_channel_id).send("Vai mesmo me forçar entrar com ELE aí? Péssimo dia pra ser escravo musical.")
                    self.who_is_in_voice.append(user_id)
                time = 0
                #loop para ver se o bot ta tocando algo ou nao.
                while True:
                    await asyncio.sleep(1)
                    time = time + 1
                    #se começar a tocar ou a musica for pausada, a contagem é reiniciada
                    if voice.is_playing() and not voice.is_paused():
                        time = 0
                        #se deu 120 segundos, ele sai do canal
                    if time == 120:
                        await self.bot.get_channel(self.music_channel_id).send("Vão me deixar no vacuo? Vou embora então. Bai")
                        await voice.disconnect()
                        self.clean_all_configs()
                    if not voice.is_connected():
                        break

            elif after.channel is None:
                #o bot saiu do canal por algum motivo. entao reseta todas as configs
                self.clean_all_configs()

    def clean_all_configs(self):
        """
            Reseta todas as variáveis
        """

        self.is_playing = False
        self.music_atual_time = ""
        self.skiping = False
        self.music_queue = []
        self.np_is_running = False
        self.now_playing = ""
        self.voice_channel = ""
        self.voice_channel_id = ""
        self.music_stop_counter = False
        self.voice_source = ""
        self.who_is_in_voice = []
    
    def extract_url_from_playlist(self, url, context, voice_channel):
        #extract playlist id from url
        query = parse_qs(urlparse(url).query, keep_blank_values=True)
        playlist_id = query["list"][0]

        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = self.GOOGLE_API_KEY)

        request = youtube.playlistItems().list(
            part = "snippet",
            playlistId = playlist_id,
            maxResults = 50
        )
        response = request.execute()

        playlist_items = []
        while request is not None:
            response = request.execute()
            playlist_items += response["items"]
            request = youtube.playlistItems().list_next(request, response)

        timestamp = datetime.datetime.utcnow()
        for t in playlist_items:
            song = {
                "title": t["snippet"]["title"],
                "requested_by": context.author,
                "display_name": context.author.display_name,
                "video_url": f'{self.youtube_url}{t["snippet"]["resourceId"]["videoId"]}',
                "timestamp": timestamp,
                "from_playlist": True
            }

            self.music_queue.append([song, voice_channel])

    def find_url_youtube(self, url, context, from_playlist=False):
        """
            Baixa pela url (ou nome da musica) o audio da musica

            param url: url ou nome da musica
            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc

            :return: dicionário com todas as informações relevantes da música
        """

        with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % url, download=False)["entries"][0]
            except Exception:
                return False

            #algumas músicas não possuem essas info. try/catch pra nao floodar esse erro nos logs
            try:
                info_track = info["track"]
            except Exception:
                info_track = "sem info"
            try:
                info_artist = info["artist"]
            except Exception:
                info_artist = "sem info"
            try:
                thumb = info["thumbnail"]
            except Exception:
                thumb = None

            requested_by = context.author
            display_name = context.author.display_name
            timestamp = datetime.datetime.utcnow()
            if from_playlist:
                requested_by = from_playlist["requested_by"]
                display_name = from_playlist["display_name"]
                timestamp = from_playlist["timestamp"]

        return {
            "source": info["formats"][0]["url"],
            "title":  info["title"],
            "description": info["description"],
            # porcamente tira o (Ao Vivo) para facilitar encontrar a letra
            "track": info_track.split("(Ao Vivo)")[0],
            # porcamente tira o FEAT. para facilitar encontrar a letra
            "artist": info_artist.split("FEAT.")[0],
            "requested_by": requested_by,
            "display_name": display_name,
            "thumbnail": thumb,
            "video_url": f"{self.youtube_url}{info['webpage_url_basename']}",
            "video_duration": info["duration"],
            # guardar o horário que a música foi pedida
            "timestamp": timestamp,
            "from_playlist": from_playlist
        }

    def play_next(self, context):
        """
            Toca a próxima música da lista de músicas
        """

        if len(self.music_queue) > 0 and not self.skiping:
            self.np_is_running = False
            #sempre que uma música iniciar, para a atualização de qualquer card do comando !np
            self.music_stop_counter = True
            self.music_atual_time = 0

            self.start_time = 0
            self.is_playing = True
            
            if self.music_queue[0][0]["from_playlist"]:
                url = self.music_queue[0][0]["video_url"]
                self.music_queue[0][0] = self.find_url_youtube(url, context, self.music_queue[0][0])

            first_url = self.music_queue[0][0]["source"]

            self.now_playing = self.music_queue[0][0]
            
            #exclui a musica da lista
            self.music_queue.pop(0)

            self.voice_source = musics.SourcePlaybackCounter(discord.FFmpegPCMAudio(first_url, **self.FFMPEG_OPTIONS), int(self.now_playing["video_duration"]))
            #da o play na música
            #after: quando terminar de tocar, vai chamar novamente a funcao play_next
            self.voice_channel.play(
                self.voice_source.voice_source,
                after=lambda e: self.play_next(context)
            )
            self.voice_source.is_source_playing = True
            self.voice_source.is_source_paused = False
        else:
            self.is_playing = False
            self.skiping = False

    async def play_music(self, music_n, context):
        """
            Toca a primeira música, ou força a execução de outra (pelo skip)

            param music_n: índice da música escolhida para o skip (ou 0, caso seja a primeira)
        """

        if len(self.music_queue) > 0:
            self.np_is_running = False
            self.start_time = 0
            self.music_atual_time = 0

            self.is_playing = True
            
            if self.music_queue[music_n][0]["from_playlist"]:
                url = self.music_queue[music_n][0]["video_url"]
                self.music_queue[music_n][0] = self.find_url_youtube(url, context, self.music_queue[music_n][0])

            first_url = self.music_queue[music_n][0]["source"]

            #tenta conectar ao canal se ainda nao tiver conectado
            if self.voice_channel == "" or not self.voice_channel.is_connected():
                self.voice_channel = await self.music_queue[music_n][1].connect()
                time.sleep(0.5)
            else:
                await self.voice_channel.move_to(self.music_queue[music_n][1])

            self.now_playing = self.music_queue[music_n][0]
            
            #exclui a musica da lista
            self.music_queue.pop(music_n)
            
            self.voice_source = musics.SourcePlaybackCounter(discord.FFmpegPCMAudio(first_url, **self.FFMPEG_OPTIONS), int(self.now_playing["video_duration"]))
            #da o play na música
            #after: quando terminar de tocar, vai chamar novamente a funcao play_next
            self.voice_channel.play(
                self.voice_source.voice_source,
                after=lambda e: self.play_next(context)
            )

            self.voice_source.is_source_playing = True
            self.voice_source.is_source_paused = False
        else:
            self.is_playing = False

    @commands.command()
    async def help(self, context):
        """
            -help: Lista como usar os comandos

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
        """

        embed = discord.Embed(
            title="Como usar essa bagaça",
            description="Comandos atualmente funcionais:",
            colour=context.author.colour,
        )

        embed.add_field(
            name='-help',
            value='Isso aqui que cê ta vendo')
        embed.add_field(
            name='-p <nome da musica>',
            value='Escutar a musiquinha que vc quer. Por enquanto não funfa playlist :(')
        embed.add_field(
            name='-q',
            value='Mostra as músicas que estão em espera na fila')
        embed.add_field(
            name='-skip',
            value='Pula pra próxima música')
        embed.add_field(
            name='-skipto <numero>',
            value='Pula pra música desejada')
        embed.add_field(
            name='-pause',
            value='Pausa a música atual (a próxima que não é, né)')
        embed.add_field(
            name='-resume',
            value='Retorna do pause (me obrigaram a não usar unpause)')
        embed.add_field(
            name='-dc',
            value='Chuta o bot do canal')
        embed.add_field(
            name='-lyrics',
            value='Mostra a letra da música atual (porcamente ainda)')
        embed.add_field(
            name='-lyrics <nome da musica#artista>',
            value='Mostra a letra da música desejada (porcamente ainda)')
        embed.add_field(
            name='-clear',
            value='Limpa a lista de músicas')
        embed.add_field(
            name='-remove <musica>',
            value='Remove a música (passa o índice, não o nome, porfa')
        embed.add_field(
            name='-np',
            value='Mostra a música atual')
        embed.add_field(
            name='-s',
            value='Salva a música atual na tua playlist.')
        embed.add_field(
            name='-mp',
            value='Mostra tua playlist.')
        embed.add_field(
            name='-rp <numero>',
            value='Remove música da playlist. O número pode ser único, ou vários separados por virgula. \
            Exemplos:\n-rp 1 (remove a música de número 1)\n-rp 1,5,7 (remove as músicas de número 1, 5 e 7)')
        embed.add_field(
            name='-pp <numero>',
            value='Coloca as músicas da playlist na queue de músicas. O número não é obrigatório e pode ser único ou vários separados por virgula. \
            Exemplos:\n-pp (coloca todas as músicas na queue)\n-pp 1 (coloca a música de número 1 na queue)\n-pp 1,5,7 (coloca as músicas de número 1, 5 e 7 na queue)')
        embed.add_field(
            name='-veia',
            value='Abre o jogo da velha (os dois players precisam dar o comando)')
    
        await context.send(embed=embed)
        self.np_is_running = False

    @commands.command()
    async def p(self, context, *args):
        """
            -p: dar play em uma música

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
            param args: argumentos passados após o comando
        """

        self.np_is_running = False

        query = " ".join(args)
        if query == "":
            await context.send("Ta quereno que eu toque o que?")
            return

        #salva o canal que o usuario esta
        try:
            if self.bot_request and self.bot.voice_clients:
                voice_channel = self.bot.voice_clients[0].channel
                self.bot_request = False
            else:
                voice_channel = context.author.voice.channel
        except AttributeError:
            await context.send("Você precisa ta num canal, lerdão. Vai escutar como?")
        else:
            if self.voice_channel == "" or voice_channel.id == self.voice_channel_id:
                if self.voice_channel_id == "":
                    self.voice_channel_id = voice_channel.id
                    self.music_queue.append([self.gabi_oini, voice_channel])

                #se tiver isso, provavelmente o individuo ta querendo uma playlist
                if "playlist?list" in query:
                    self.extract_url_from_playlist(query, context, voice_channel)
                    await context.send("Acredito que toda caralhada da playlist tá na queue. Se não tiver, fodase.")
                else:
                    song = self.find_url_youtube(query, context)
                    #a função tem dois returns de tipos diferentes. Foi o jeito q pensei na hora. deve ter jeito melhor
                    if type(song) == type(True):
                        await context.send("Nao consegui achá :O.")
                        return

                    #manda mensagem específica caso tenha alguma palavra chave encontrada na descrição da música
                    for key, value in self.pode_ser_alguem.items():
                        for key_wrod in value["keys"]:
                            substr = re.escape(key_wrod)
                            if re.compile(fr'\b{substr}\b', flags=re.I).findall(song["description"]):
                                await context.send(value["frase"])
                                break

                    await context.send("%s adicionada a fila" % song["title"])
                    self.music_queue.append([song, voice_channel])

                if not self.is_playing:
                    await self.play_music(0, context)
            else:
                await context.send(f"{context.author.display_name}, o bot ta se divertindo com os de vdd em outro canal. Vai ficar sozinho aí :D")

    @commands.command()
    async def q(self, context):
        """
            -q: mostrar a lista de músicas dividida em paginas (10 musicas por pagina)

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
        """

        self.np_is_running = False

        retval = "```"
        all_music_pages = []
        embed = discord.Embed(
            title="Iremoví depois:",
            description=f"Temo {len(self.music_queue)} músicas"
        )
        for i in range(0, len(self.music_queue)):
            music_name = self.music_queue[i][0]["title"]
            requested_by = str(self.music_queue[i][0]["requested_by"])
            requested_by_display_name = self.music_queue[i][0]["display_name"]

            timestamp = self.music_queue[i][0]['timestamp'].strftime('%H:%M')
            embed.add_field(
                name=f"{i + 1} - {music_name}",
                value=f"{requested_by_display_name} ({requested_by}) • Hoje às {timestamp}",
                inline=False)
            
            retval += f"{i} \n"
            
            #a cada 10 musicas, adiciona uma pagina de musicas
            if (i+1) % 10 == 0 and i != 0:
                retval += "```"
                all_music_pages.append(embed)
                
                embed = discord.Embed(
                    title="Iremoví depois:",
                    description=f"Temo {len(self.music_queue)} músicas"
                )

                retval = "```"

        retval += "```"
        if "``````" in retval:
            retval = ""
        if retval != "":
            all_music_pages.append(embed)
        elif retval == "" and len(all_music_pages) == 0:
            await context.send("Tem nada aqui irmão")
            return

        pages = len(all_music_pages)
        cur_page = 1
        prev_page = cur_page
        message = await context.send(embed=all_music_pages[cur_page-1])
        
        #coloca as reações após as musicas
        await message.add_reaction("⏮")
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        await message.add_reaction("⏭")

        def check(reaction, user):
            """
                Ter a certeza de que somente as reações do usuário que chamou o comando serão processadas

                param reaction: reação dada na mensagem
                param user: usuário que reagiu
            """

            return user == context.author and str(reaction.emoji) in ["◀️", "▶️", "⏮", "⏭"]

        while True:
            try:
                prev_page = cur_page
                #espera por 20 segundos (timeout) até receber alguma reação. apaga a mensagem se nao houver
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
                    #remove reação se estiver na ultima/primeira posicao e a pessoa tentar forçar
                    await message.remove_reaction(reaction, user)

                #atualiza a página (mensagem)
                if prev_page != cur_page:
                   await message.edit(embed=all_music_pages[cur_page-1])
                   await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                try:
                    await message.delete()
                except Exception:
                    pass
                #acaba com o loop após o timeout
                break

    @commands.command()
    async def skip(self, context):
        """
            -skip: pula pra próxima música

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
        """
        
        self.np_is_running = False
    
        if self.voice_channel != "":
            if len(self.music_queue) >= 0:
                self.voice_channel.stop()
                self.skiping = True
                await self.play_music(0, context)
            else:
                await context.send("Tem música o suficiente pra isso não. Da um queue antes aí.")
 
    @commands.command()
    async def skipto(self, context, *args):
        """
            -skipto: pula pra uma música específica

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
            param args: argumentos passados após o comando
        """

        self.np_is_running = False

        music_n = " ".join(args)
        if self.voice_channel != "":
            if len(self.music_queue) >= int(music_n):
                self.voice_channel.stop()
                self.skiping = True
                await self.play_music(int(music_n) - 1, context)
            else:
                await context.send("Tem música o suficiente pra isso não. Da um queue antes aí.")

    @commands.command()
    async def pause(self, context):
        """
            -pause: pausa a musica

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
        """

        self.np_is_running = False

        if self.is_playing:
            self.voice_channel.pause()
            self.is_playing = False
            self.voice_source.is_source_paused = True

    @commands.command()
    async def resume(self, context):
        """
            -resume: continua a musica pausada

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
        """

        self.np_is_running = False

        if not self.is_playing:
            self.voice_channel.resume()
            self.is_playing = True
            self.voice_source.is_source_paused = False

    @commands.command()
    async def dc(self, context):
        """
            -dc: desconecta o bot da sala

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
        """

        self.np_is_running = False
    
        if not context.author.voice:
            await context.send("Cê nem ta no canal. Quer expulsar o bot pq, cusão?")
            return

        if not context.voice_client:
            await context.send("Limpando a sujeira da última party...")
            self.clean_all_configs()
            await context.voice_client.disconnect()

            return

        if context.author.voice.channel != context.voice_client.channel:
            await context.send("Cê nem ta no canal. Quer expulsar o bot pq, cusão?")
        else:
            await context.send("Toino lá. Vlw Flws :3")
            self.clean_all_configs()
            await context.voice_client.disconnect()

    @commands.command()
    async def lyrics(self, context, *args):
        """
            -lyrics: mostra a letra da musica atual ou de uma especifica

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
            param args: argumentos passados após o comando
        """

        self.np_is_running = False

        music_info = ":".join(args).replace(":", " ").split("#")

        #se foi passado dois parametros no comando (levando em conta o separador #), busca a musica pedida
        if len(music_info) == 2:
            music_name = music_info[0]
            music_artist = music_info[1]
        #caso o numero de parametros passados estejam errados
        elif len(music_info) != 2 and len(music_info) != 1:
            await context.send("Para uma música específica, deve ser pesquisada como: ```nome da musica#artista```")
            return
        #se passou somente o comando, busca a letra da musica que está tocando
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

        embed.set_author(name=music_artist)
        await context.send(embed=embed)

    @commands.command()
    async def clear(self, context):
        """
            -clear: limpa a lista de musicas

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
            param args: argumentos passados após o comando
        """

        self.np_is_running = False
            
        if not context.author.voice:
            await context.send("Cê nem ta no canal. Quer excluir as músicas pq?")
            return

        if not context.voice_client:
            await context.send("Limpando as músicas da última party...")
            self.music_queue = []

            return

        if context.author.voice.channel != context.voice_client.channel:
            await context.send("Cê nem ta no canal. Quer excluir as músicas pq?")
        else:
            self.music_queue = []
            await context.send("Lista de músicas nova em folha")
  
    @commands.command()
    async def remove(self, context, *args):
        """
            -remove: mostra a letra da musica atual ou de uma especifica

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
            param args: argumentos passados após o comando
        """

        self.np_is_running = False

        music_n = int(" ".join(args))
        if not context.author.voice:
            await context.send("Cê nem ta no canal. Quer excluir a música pq?")
            return

        if not context.voice_client:
            await context.send("Não quero")
            return

        if context.author.voice.channel != context.voice_client.channel:
            await context.send("Cê nem ta no canal. Quer excluir a música pq?")
        else:
            #verifica se está em algum canal de voz
            if self.voice_channel != "":
                if len(self.music_queue) >= music_n:
                    self.music_queue.pop(music_n - 1)

            await context.send("Pronto. Foi pro lixo.")

    @commands.command()
    async def np(self, context):
        """
            -np: musica tocando na hora

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
            param args: argumentos passados após o comando
        """

        #precaução caso haja algum comando -np executado anteriormente e a música desse card ainda não acabou
        #isso faz com que o loop desse card finalize, e a atualização do tempo decorrido da música pare
        self.voice_source.np_command = True
        self.np_is_running = False

        #verifica se está em algum canal de voz
        if self.voice_channel != "" and self.now_playing["artist"] != "Gabi suprema":
            embed = discord.Embed(
                title="Tamovino agora:",
                colour=context.author.colour,
                timestamp=self.now_playing["timestamp"]
            )

            music_name = self.now_playing["title"]
            music_artist = self.now_playing["artist"]

            requested_by = str(self.now_playing["requested_by"])
            requested_by_display_name = self.now_playing["display_name"]
            requested_by_avatar_url = self.now_playing["requested_by"].avatar_url

            current_time = divmod(self.get_music_progress(), 60)
            music_duration = divmod(int(self.now_playing["video_duration"]), 60)

            show_time = f"{int(current_time[0])}:{round(current_time[1]):02}/{int(music_duration[0])}:{round(music_duration[1]):02}"

            embed.set_footer(
                text=f"Pedida por: {requested_by_display_name} ({requested_by})",
                icon_url=requested_by_avatar_url
            )
            embed.add_field(name="Título:", value=f"[{music_name}]({self.now_playing['video_url']})", inline=False)
            embed.add_field(name="Artista:", value=music_artist, inline=False)
            embed.add_field(name="Duração:", value=f"{show_time}", inline=False)

            try:
                embed.set_thumbnail(url=self.now_playing["thumbnail"])
            except discord.errors.HTTPException:
                pass

            message = await context.send(embed=embed)

            self.voice_source.np_command = False
            #após realizar a configuração inicial do card da música atual, seta a flag que irá manter
            #o loop que atualiza o tempo decorrido da música
            self.np_is_running = True

            #TODO: o while irá atualizar somente o tempo decorrido da música. Mas por se tratar de cards,
            #toda sua estrutura deve ser refeita. Por isso a repetição do código do início do método
            time.sleep(1)
            while self.np_is_running:
                current_time = divmod(self.get_music_progress(), 60)

                show_time = f"{int(current_time[0])}:{round(current_time[1]):02}/{int(music_duration[0])}:{round(music_duration[1]):02}"

                new_embed = discord.Embed(
                    title="Tamovino agora:",
                    colour=context.author.colour,
                    timestamp=self.now_playing["timestamp"]
                )
                new_embed.set_footer(
                    text=f"Pedida por: {requested_by_display_name} ({requested_by})",
                    icon_url=requested_by_avatar_url
                )
                new_embed.add_field(name="Título:", value=f"[{music_name}]({self.now_playing['video_url']})", inline=False)
                new_embed.add_field(name="Artista:", value=music_artist, inline=False)
                new_embed.add_field(name="Duração:", value=f"{show_time}", inline=False)

                try:
                    new_embed.set_thumbnail(url=self.now_playing["thumbnail"])
                except discord.errors.HTTPException:
                    pass

                await message.edit(embed=new_embed)
                time.sleep(1)

    @commands.command()
    async def s(self, context):
        rows = self.database.select_rows_dict_cursor(
            "SELECT * FROM USERS WHERE USERID = '{}'".format(context.author.id), True)

        try:
            timestamp = datetime.datetime.utcnow().strftime('%d/%m/%Y - %H:%M')
            if self.now_playing["title"] == "Gabi oini":
                await context.send("Impossiboru salvar a músca da Gabier")
                return
            music_info = {
                self.now_playing["video_url"]: {"title": self.now_playing["title"], "timestamp": timestamp}
            }
            await context.send(f"{self.now_playing['title']} salva na tua playlist :D")
        except Exception as e:
            await context.send("Tem música tocando não. Vou por na playlist como?")
        else:
            #usuário não tá no bd. insere o ID dele e a musica atual como a playlist
            if not bool(rows):
                self.database.commit_query(
                    "INSERT INTO USERS (USERID, PLAYLISTS) VALUES \
                        ('{}', {})".format(context.author.id, psycopg2.extras.Json(music_info))
                )
            else:
                #pego as músicas já salvas e atualizo
                playlist = self.database.select_rows_dict_cursor(
                    "SELECT PLAYLISTS FROM USERS WHERE USERID = '{}'".format(context.author.id), True)
                
                update_playlist = {}
                for musics in playlist[0]:
                    for url, title in musics.items():
                        update_playlist[url] = title

                timestamp = datetime.datetime.utcnow().strftime('%d/%m/%Y - %H:%M')
                update_playlist[self.now_playing["video_url"]] = {"title": self.now_playing["title"], "timestamp": timestamp}

                self.database.commit_query(
                    "UPDATE USERS SET PLAYLISTS = {} WHERE USERID = '{}'".format(
                        psycopg2.extras.Json(update_playlist), context.author.id)
                )

    @commands.command()
    async def mp(self, context):
        """
            -mypl: mostrar a lista de músicas da playlist do usuário

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
        """

        playlist = self.database.select_rows_dict_cursor(
                        "SELECT PLAYLISTS FROM USERS WHERE USERID = '{}'".format(context.author.id), True)

        if not bool(playlist):
            await context.send("Parece que vc não criou uma playlist ainda... Ou eu a perdi :3")
            return

        playlist_musics = []
        for musics in playlist[0]:
            for url, title in musics.items():
                playlist_musics.append([title, url])

        self.np_is_running = False

        retval = "```"
        all_music_pages = []
        embed = discord.Embed(
            title=f"Playlist de {context.author.display_name}",
            description=f"Temo {len(playlist_musics)} músicas"
        )
        for musics in playlist[0]:
            i = 0
            for url, title in musics.items():
                timestamp = title["timestamp"]
                embed.add_field(
                    name=f"{i + 1} - {title['title']}",
                    value=f"Salva em: {timestamp}",
                    inline=False)
                
                retval += f"{i} \n"
            
                #a cada 10 musicas, adiciona uma pagina de musicas
                if (i+1) % 10 == 0 and i != 0:
                    retval += "```"
                    all_music_pages.append(embed)
                    
                    embed = discord.Embed(
                        title=f"Playlist de {context.author.display_name}",
                        description=f"Temo {len(playlist_musics)} músicas"
                    )

                    retval = "```"
                
                i += 1

        retval += "```"
        if "``````" in retval:
            retval = ""
        if retval != "":
            all_music_pages.append(embed)
        elif retval == "" and len(all_music_pages) == 0:
            await context.send("Parece que vc não criou uma playlist ainda... Ou eu a perdi :3")
            return

        pages = len(all_music_pages)
        cur_page = 1
        prev_page = cur_page
        message = await context.send(embed=all_music_pages[cur_page-1])
        
        #coloca as reações após as musicas
        await message.add_reaction("⏮")
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        await message.add_reaction("⏭")

        def check(reaction, user):
            """
                Ter a certeza de que somente as reações do usuário que chamou o comando serão processadas

                param reaction: reação dada na mensagem
                param user: usuário que reagiu
            """

            return user == context.author and str(reaction.emoji) in ["◀️", "▶️", "⏮", "⏭"]

        while True:
            try:
                prev_page = cur_page
                #espera por 20 segundos (timeout) até receber alguma reação. apaga a mensagem se nao houver
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
                    #remove reação se estiver na ultima/primeira posicao e a pessoa tentar forçar
                    await message.remove_reaction(reaction, user)

                #atualiza a página (mensagem)
                if prev_page != cur_page:
                   await message.edit(embed=all_music_pages[cur_page-1])
                   await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                try:
                    await message.delete()
                except Exception:
                    pass
                #acaba com o loop após o timeout
                break
    
    @commands.command()
    async def pp(self, context, *args):
        """
            -pp: adicionar a playlist do usuário na queue de música

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
        """

        music_n = " ".join(args).split(',')

        playlist = self.database.select_rows_dict_cursor(
                        "SELECT PLAYLISTS FROM USERS WHERE USERID = '{}'".format(context.author.id), True)

        if not bool(playlist):
            await context.send("Parece que vc não criou uma playlist ainda... Ou eu a perdi :3")
            return

        #salva o canal que o usuario esta
        try:
            voice_channel = context.author.voice.channel
        except AttributeError:
            await context.send("Você precisa ta num canal, lerdão. Vai escutar como?")
            return

        for musics in playlist[0]:
            i = 1
            for url, title in musics.items():
                if str(i) in music_n or music_n[0] == "":
                    song = {
                        "title": title["title"],
                        "requested_by": context.author,
                        "display_name": context.author.display_name,
                        "video_url": url,
                        "timestamp": datetime.datetime.utcnow(),
                        "from_playlist": True
                    }

                    self.music_queue.append([song, voice_channel])

                i += 1

        #se as musicas ja pararam, começa novamente
        if not self.is_playing:
            await self.play_music(0, context)

    @commands.command()
    async def rp(self, context, *args):
        """
            -rp: remove a música da playlist

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
            param args: argumentos passados após o comando
        """

        self.np_is_running = False

        music_n = " ".join(args).split(',')

        playlist = self.database.select_rows_dict_cursor(
                        "SELECT PLAYLISTS FROM USERS WHERE USERID = '{}'".format(context.author.id), True)

        if not bool(playlist):
            await context.send("Parece que vc não criou uma playlist ainda... Ou eu a perdi :3")
            return

        update_playlist = {}
        for musics in playlist[0]:
            i = 1
            for url, title in musics.items():
                if str(i) not in music_n:
                    update_playlist[url] = title
                
                i += 1

        self.database.commit_query(
            "UPDATE USERS SET PLAYLISTS = {} WHERE USERID = '{}'".format(
                psycopg2.extras.Json(update_playlist), context.author.id)
        )

    @commands.command()
    async def shuffle(self, context):
        """
            -shuffle: randomiza as músicas na queue

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
        """

        self.np_is_running = False

        if not context.author.voice:
            await context.send("Cê nem ta no canal. Vai mudar a queue não.")
            return

        if not context.voice_client:
            await context.send("Não quero")
            return

        if context.author.voice.channel != context.voice_client.channel:
            await context.send("Cê nem ta no canal. Vai mudar a queue não.")
        else:
            #verifica se está em algum canal de voz
            if self.voice_channel != "":
                #se tiver música na queue, salva a original e aplica um shuffle nela
                if len(self.music_queue) > 0:
                    self.save_music_queue = []
                    self.save_music_queue = self.music_queue.copy()
                    random.shuffle(self.music_queue)

            await context.send("Pronto. Embaraiei tudo.")    

    @commands.command()
    async def original(self, context):
        """
            -original: randomiza as músicas na queue

            param context: contexto enviado ao bot com informações do servidor, autor do comando, etc
        """

        self.np_is_running = False

        if not context.author.voice:
            await context.send("Cê nem ta no canal. Vai mudar a queue não.")
            return

        if not context.voice_client:
            await context.send("Não quero")
            return

        if context.author.voice.channel != context.voice_client.channel:
            await context.send("Cê nem ta no canal. Vai mudar a queue não.")
        else:
            #verifica se está em algum canal de voz
            if self.voice_channel != "":
                #se tiver música na queue, salva a original e aplica um shuffle nela
                if len(self.music_queue) > 0:
                    self.music_queue = []
                    self.music_queue = self.save_music_queue.copy()

            await context.send("Pronto. Desembaraiei tudo.")
