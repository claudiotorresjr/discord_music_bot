import threading
import discord
import time

#musica com 30 segundos pra teste
#https://www.youtube.com/watch?v=E9lwxyqVxi4 Big & Small Theme (Lyric Video)

class SourcePlaybackCounter(discord.AudioSource):
    """
        Classe base para o player de música
    """

    def __init__(self, source, music_duration):
        """
            inicializa o player de música

            param source: o player de música
            param music_duration: duração da música em segundos
            param music_duration: duração da música em segundos
        """

        self.voice_source = source
        self.music_progress = 0
        self.music_duration = music_duration

        self.source_started = False
        self.is_source_playing = False
        self.is_source_paused = True
    
        self.voice_source.np_command = False
        self.thread = threading.Thread(
            target=self.music_time_counter
        )
        self.thread.start()


    def music_time_counter(self):
        """
            cria um contador de segundos para marcar o tempo de execução da música sendo tocada.
            Não é 100% exato, mas da pra ter uma ideia
        """

        self.source_started = True
        #o contador de tempo fica atualizando os segundos se a musica estiver ativa e enquanto o contador
        #não for superior ao tempo total da música e se a música ainda está tocando ou pausada
        while self.source_started and (self.music_progress <= self.music_duration) and (self.is_source_playing or self.is_source_paused):
            #se estiver pausada, não atualiza o contador
            if not self.is_source_paused:
                time.sleep(1)
                self.music_progress += 1

        self.source_started = False