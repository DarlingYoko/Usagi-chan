import sys, discord, os, subprocess, random, time
from youtube_dl import YoutubeDL
from gtts import gTTS
from threading import Thread
from random import randint
import spotipy
import spotipy.oauth2 as oauth2
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from youtube_search import YoutubeSearch

class MusicPlayer():
    def __init__(self):
        self.vc = None
        self.repeat = None
        self.pause = None
        self.queryList = []
        self.queryData = {}
        self.lastAudio = None
        self.count = 0
        CLIENT_ID = '118b5bcd3192449282a6618c19f70d50'
        CLIENT_SECRET = '6d3496fc16f54a1586036c06a813894a'

        auth_manager = SpotifyClientCredentials(client_id = CLIENT_ID,
                                                client_secret = CLIENT_SECRET)


        self.sp = spotipy.Spotify(auth_manager = auth_manager)

    def play(self, msg, command):
        URL = msg.split(command)[1].strip()
        answer = 'Не получилось добавить трек в очередь( Пипакрай'
        if 'youtube' in URL:
            answer = self.getYoutube(URL)

        elif 'spotify' in URL:
            answer = self.getSpoti(URL)

        else:
            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
            self.vc.play(discord.FFmpegPCMAudio(URL, executable = 'C:/FFMPEG/ffmpeg.exe', **FFMPEG_OPTIONS))

        return answer

    def pauseAudio(self):
        self.vc.pause()
        self.pause = True

    def resume(self):
        self.vc.resume()
        self.pause = False

    def stop(self):
        self.vc.stop()
        self.repeat = None
        self.queryList = []
        self.lastAudio = None

    def shuffle(self):
        random.shuffle(self.queryList)

    def nowPlay(self):
        answer = 'Ничего не играет'
        if self.lastAudio:
            answer = 'Сейчас играет - {0}'.format(self.queryData[self.lastAudio]['title'])
        return answer

    def skip(self):
        if len(self.queryList) > 0:
            if self.vc.is_playing():
                self.vc.stop()
                del self.queryData[self.lastAudio]

            answer = 'Песенка скипнута\nСейчас играет - {0}'.format(self.queryData[self.queryList[0]]['title'])
        else:
            self.vc.stop()
            self.lastAudio = None
            answer = 'Больше песенок нет('
        return answer

    def query(self):
        queryList = ['{0}. {1}'.format(i+1, self.queryData[self.queryList[i]]['title']) for i in range(len(self.queryList))]
        if len(self.queryList) == 0 and not self.lastAudio:
            answer = 'Пусто('
        else:
            answer = 'Сейчас играет - {0}\n{1}'.format(self.queryData[self.lastAudio]['title'], '\n'.join(queryList))
        return answer

    def repeat(self, msg, command):
        if msg.split(command)[1].strip() == 'last':
            self.repeat = 1
            answer = 'Буду повторять песню'
        else:
            self.repeat = None
            answer = 'Больше не повторяю песню'
        return answer

    async def connect(self, client, msg, command):
        channel = await client.fetch_channel(msg.split(command)[1].strip())
        self.vc = await channel.connect()

    def getSpoti(self, URL):
        print(URL)
        trackID = URL[31:54]
        trackInfo = self.sp.track(trackID)

        track = trackInfo['album']['artists'][0]['name'] + ' ' + trackInfo['album']['name']

        results = YoutubeSearch(track, max_results=1).to_dict()

        return self.getYoutube('https://www.youtube.com' + results[0]['url_suffix'])


    def getYoutube(self, URL):
        #ydl_opts = {'format': 'bestaudio'}
        with YoutubeDL() as ydl:
            info = ydl.extract_info(URL, download=False)
            URL = info['formats'][0]['url']
            title = info['title']
            duration = info['duration']

        track = 'Track {}'.format(self.count)
        self.count += 1
        self.queryList.append(track)
        self.queryData[track] = {
                            'title': title,
                            'URL': URL,
                            'duration': duration,
                            }

        return 'Добавила трек в очередь, Нья!'



    def simpleVoice(self, msg, command):
        file = '../audio/message.mp3'
        language = 'ru'
        speech = gTTS(text = msg.split(command)[1], lang = language, slow = False)
        speech.save(file)
        self.vc.play(discord.FFmpegPCMAudio(source = file), after=lambda e: print(f'music in channel has finished playing.'))

    def checkPlay(self):
        try:
            if not self.vc.is_playing() and self.repeat and self.lastAudio and not self.pause:
                self.vc.play(discord.FFmpegPCMAudio(source = self.lastAudio))

            elif not self.vc.is_playing() and not self.repeat and len(self.queryList) > 0 and not self.pause:
                if self.lastAudio:
                    del self.queryData[self.lastAudio]
                self.lastAudio = self.queryList.pop(0)
                print('начинаю играть')

                FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
                self.vc.play(discord.FFmpegPCMAudio(self.queryData[self.lastAudio]['URL'], executable = 'C:/FFMPEG/ffmpeg.exe', **FFMPEG_OPTIONS))

        except Exception as e:
            pass
