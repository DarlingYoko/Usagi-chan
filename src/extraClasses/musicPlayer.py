import sys, discord, os, subprocess, random, time, asyncio, aiohttp
from youtube_dl import YoutubeDL
from gtts import gTTS
from threading import Thread
from random import randint
import spotipy
import spotipy.oauth2 as oauth2
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from youtube_search import YoutubeSearch
from src.functions import createEmbed, getCurrentTime




class MusicPlayer():
    def __init__(self, client, config):
        self.vc = None
        self.repeat = None
        self.pause = None
        self.queryList = []
        self.queryData = {}
        self.lastAudio = None
        self.count = 0
        self.client = client
        self.config = config
        self.reacts = {1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣'}
        CLIENT_ID = '118b5bcd3192449282a6618c19f70d50'
        CLIENT_SECRET = '6d3496fc16f54a1586036c06a813894a'

        auth_manager = SpotifyClientCredentials(client_id = CLIENT_ID,
                                                client_secret = CLIENT_SECRET)


        self.sp = spotipy.Spotify(auth_manager = auth_manager)

    async def play(self, msg, command, message):
        URL = msg.split(command)[1].strip()
        user = message.author.name.split('#')[0]
        answer = 'Не получилось добавить трек в очередь( Пипакрай'
        channel = message.channel
        loop = asyncio.get_running_loop()


        if 'youtube' in URL:
            #await loop.run_in_executor(None, self.getYoutube(URL, user))
            #self.client.loop.create_task(self.getYoutube(URL, user))
            await self.getYoutube(URL, user)
            answer = ''


        elif 'spotify' in URL:
            #Thread(target = asyncio.run, args=(self.getSpoti(URL, user), )).start()
            #await loop.run_in_executor(None, self.getSpoti(URL, user))
            await self.getSpoti(URL, user)
            #self.client.loop.create_task(self.getSpoti(URL, user))
            answer = ''


        else:
            title = 'Выбор трека'
            trackID = -1
            results = YoutubeSearch(URL, max_results=5).to_dict()
            description = '\n\n'.join(['{0}. {1} **[{2}]**'.format(i+1, results[i]['title'], results[i]['duration']) for i in range(5)])
            footer = 'По МСК ' + getCurrentTime()
            embed = createEmbed(title = title, description = description, footer = footer, color = 0xf08080)
            question = await channel.send(embed = embed)
            for i in range(len(self.reacts)):
                await question.add_reaction(self.reacts[i + 1])

            def check(reaction, user):
                return user == message.author and str(reaction.emoji) in self.reacts.values()

            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
            except:
                title = 'Ты не выбрал трек за отведённое время, бака!'
                description = ''

            else:

                for key, value in self.reacts.items():
                    if value == str(reaction.emoji):
                        trackID = key - 1

                title = 'Трек под номером {} добавляется в очередь, Нья!'.format(reaction)
                description = '{0} **[{1}]**'.format(results[trackID]['title'], results[trackID]['duration'])


            answer = ''


            embed = createEmbed(title = title, description = description, footer = footer, color = 0xe00000)
            await question.edit(embed = embed)
            await question.clear_reactions()
            if trackID != -1:
                await self.getYoutube('https://www.youtube.com' + results[trackID]['url_suffix'], user, question)



        await channel.send(answer)

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
            answer = 'Сейчас играет - **{0}**, добавил(-a) **{1}** `{2}`'.format(self.queryData[self.lastAudio]['title'],
                                                                                self.queryData[self.lastAudio]['user'],
                                                                                self.queryData[self.lastAudio]['duration'])
        return answer

    def skip(self):
        if len(self.queryList) > 0:
            self.vc.stop()
            answer = 'Песенка скипнута\nСейчас играет - **{0}**, добавил(-a) **{1}** `{2}`'.format(self.queryData[self.queryList[0]]['title'],
                                                                                                    self.queryData[self.queryList[0]]['user'],
                                                                                                    self.queryData[self.queryList[0]]['duration'],)


        else:
            self.vc.stop()
            answer = 'Больше песенок нет('
            self.lastAudio = None
        return answer

    def query(self):
        queryList = ['`[{0}]` **{1}**, добавил(-a) **{2}** `{3}`'.format(i+1,
                                                        self.queryData[self.queryList[i]]['title'],
                                                        self.queryData[self.queryList[i]]['user'],
                                                        self.queryData[self.queryList[i]]['duration'],)
                                                    for i in range(len(self.queryList))]
        if len(self.queryList) == 0 and not self.lastAudio:
            answer = 'Пусто('
        else:
            answer = 'Сейчас играет - **{0}**, добавил(-a) **{2}** `{3}`\n{1}'.format(self.queryData[self.lastAudio]['title'],
                                                                        '\n'.join(queryList),
                                                                        self.queryData[self.lastAudio]['user'],
                                                                        self.queryData[self.lastAudio]['duration'], )
        return answer

    def repeat(self, msg, command):
        if msg.split(command)[1].strip() == 'last':
            self.repeat = 1
            answer = 'Буду повторять песню'
        else:
            self.repeat = None
            answer = 'Больше не повторяю песню'
        return answer

    async def connect(self, msg, command):
        channel = await self.client.fetch_channel(msg.split(command)[1].strip())
        self.vc = await channel.connect()

    async def getSpoti(self, URL, user):
        channel = await self.client.fetch_channel(858145829158912030)

        if 'playlist' in URL:
            mes = 'Начала добавлять плейлист, Нья!'
            message = await channel.send(mes)
            playlistID = URL[34:56]
            playlist_info = self.sp.playlist_tracks(playlistID)
            res = []
            for track in playlist_info['items']:
                trackName = ''
                if track['track']['id']:
                    trackInfo = self.sp.track(track['track']['id'])
                    trackName = trackInfo['album']['artists'][0]['name'] + ' ' + trackInfo['name']
                else:
                    trackName = track['track']['name']

                results = YoutubeSearch(trackName, max_results=1).to_dict()
                print(results)
                res.append(results[0]['url_suffix'].split('/watch?v=')[1])

            url = 'https://www.youtube.com/watch_videos?video_ids='
            await self.getYoutube(url + ','.join(res), user, 1)
            answer = 'Добавила плейлист в очередь, Нья!'
            await message.edit(content = answer)


        else:
            trackID = URL[31:54]
            trackInfo = self.sp.track(trackID)
            track = trackInfo['album']['artists'][0]['name'] + ' ' + trackInfo['name']
            results = YoutubeSearch(track, max_results=1).to_dict()
            await self.getYoutube('https://www.youtube.com' + results[0]['url_suffix'], user)





    async def getYoutube(self, URL, user, question = None):

        channel = await self.client.fetch_channel(858145829158912030)

        mes = 'Начала добавлять трек , Нья!'
        answer = 'Добавила трек в очередь, Нья!'

        if 'list' in URL:
            mes = 'Начала добавлять плейлист, Нья!'
            answer = 'Добавила плейлист в очередь, Нья!'

        #ydl_opts = {'format': 'bestaudio'}

        if not question:
            message = await channel.send(mes)

        ydl_opts = {
            'ignoreerrors': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(URL, download=False)

        if 'list' in URL or 'video_ids' in URL:
            for track in info['entries']:
                self.getData(track, user)

        else:
            self.getData(info, user)


        if not question:
            await message.edit(content = answer)
        elif question != 1:
            embed = question.embeds[0].to_dict()
            embed = createEmbed(title = embed['title'][:8] + ' был выбран и добавлен в очередь, нья!',
                                description = embed['description'],
                                footer = embed['footer']['text'],
                                color = 0xf08080)
            await question.edit(embed = embed)



    def simpleVoice(self, msg, command):
        file = '../audio/message.mp3'
        language = 'ru'
        speech = gTTS(text = msg.split(command)[1], lang = language, slow = False)
        speech.save(file)
        self.vc.play(discord.FFmpegPCMAudio(source = file), after=lambda e: print(f'music in channel has finished playing.'))

    def checkPlay(self):
        try:
            if not self.vc.is_playing() and self.repeat and self.lastAudio and not self.pause:
                FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
                self.vc.play(discord.FFmpegPCMAudio(source = self.lastAudio, **FFMPEG_OPTIONS))

            elif not self.vc.is_playing() and not self.repeat and len(self.queryList) > 0 and not self.pause:
                if self.lastAudio:
                    del self.queryData[self.lastAudio]
                self.lastAudio = self.queryList.pop(0)
                print('начинаю играть')

                FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
                self.vc.play(discord.FFmpegPCMAudio(self.queryData[self.lastAudio]['URL'], **FFMPEG_OPTIONS))

        except Exception as e:
            pass


    def addTrack(self, title, URL, duration, user):
        track = 'Track {}'.format(self.count)
        self.count += 1
        self.queryList.append(track)
        self.queryData[track] = {
                            'title': title,
                            'URL': URL,
                            'duration': duration,
                            'user': user,
                            }

    def getData(self, info, user):
        URL = info['formats'][0]['url']
        title = info['title']
        duration = info['duration']
        self.addTrack(title, URL, duration, user)
