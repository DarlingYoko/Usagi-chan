import sys, discord, os, subprocess, random, time, asyncio
from youtube_dl import YoutubeDL
from gtts import gTTS
from threading import Thread
from random import randint
import spotipy
import spotipy.oauth2 as oauth2
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from youtube_search import YoutubeSearch
from src.functions import createEmbed, getCurrentTime
from discord_components import Button, ButtonStyle, InteractionType



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
        self.loop = asyncio.get_running_loop()
        self.reacts = {1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣'}
        CLIENT_ID = '118b5bcd3192449282a6618c19f70d50'
        CLIENT_SECRET = '6d3496fc16f54a1586036c06a813894a'

        auth_manager = SpotifyClientCredentials(client_id = CLIENT_ID,
                                                client_secret = CLIENT_SECRET)


        self.sp = spotipy.Spotify(auth_manager = auth_manager)

    async def play(self, msg, command, message):
        channel = await self.client.fetch_channel(self.config['data'].getint('mpChannel'))
        if message.channel != channel:
            return

        URL = msg[2:].strip()
        user = message.author.display_name.split('#')[0]
        answer = 'Не получилось добавить трек в очередь( Пипакрай'

        mes = 'Начала добавлять трек , Нья!'

        if 'list' in URL:
            mes = 'Начала добавлять плейлист, Нья!'



        if 'youtube' in URL:
            message = await channel.send(mes)
            #await loop.run_in_executor(None, self.getYoutube(URL, user))
            #self.client.loop.create_task(self.getYoutube(URL, user))
            Thread(target = asyncio.run, args=(self.getYoutube(URL, user, message = message), )).start()
            answer = ''


        elif 'spotify' in URL:
            message = await channel.send(mes)
            Thread(target = asyncio.run, args=(self.getSpoti(URL, user, message), )).start()
            #await loop.run_in_executor(None, self.getSpoti(URL, user))
            #await self.getSpoti(URL, user)
            #self.client.loop.create_task(self.getSpoti(URL, user))
            answer = ''


        else:
            title = 'Выбор трека'
            trackID = -1
            results = YoutubeSearch(URL, max_results=5).to_dict()
            description = '\n\n'.join(['{0}. {1} **[{2}]**'.format(i+1, results[i]['title'], results[i]['duration']) for i in range(5)])
            footer = 'По МСК ' + getCurrentTime()
            embed = createEmbed(title = title, description = description, footer = footer, color = 0xf08080)

            emojiOne = self.client.get_emoji(873719561562755143)
            emojiTwo = self.client.get_emoji(873653970839674941)
            emojiThree = self.client.get_emoji(873653970751602719)
            emojiFour = self.client.get_emoji(873653970839670854)
            emojiFive = self.client.get_emoji(873653970994888704)


            btn1 = Button(style=ButtonStyle.gray, emoji = emojiOne, id = '0')
            btn2 = Button(style=ButtonStyle.gray, emoji = emojiTwo, id = '1')
            btn3 = Button(style=ButtonStyle.gray, emoji = emojiThree, id = '2')
            btn4 = Button(style=ButtonStyle.gray, emoji = emojiFour, id = '3')
            btn5 = Button(style=ButtonStyle.gray, emoji = emojiFive, id = '4')
            components=[[btn1, btn2, btn3, btn4, btn5,]]

            question = await channel.send(embed = embed, components = components)

            def check(res):
                return res.channel == message.channel and res.author == message.author and res.message.id == question.id

            try:
                res = await self.client.wait_for("button_click", check = check, timeout = 60.0)

            except:
                title = 'Ты не выбрал трек за отведённое время, бака!'
                description = ''

            else:
                trackID = int(res.component.id)
                title = 'Трек под номером {} добавляется в очередь, Нья!'.format(trackID)
                description = '{0} **[{1}]**'.format(results[trackID]['title'], results[trackID]['duration'])



            answer = ''
            embed = createEmbed(title = title, description = description, footer = footer, color = 0xe00000)
            await question.edit(embed = embed, components = [])

            if trackID != -1:
                await self.getYoutube('https://www.youtube.com' + results[trackID]['url_suffix'], user, question = question, description = description)



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

    async def query(self, message):

        channel = await self.client.fetch_channel(self.config['data'].getint('mpChannel'))

        emojiStart = self.client.get_emoji(873921151896805487)
        emojiPrevious = self.client.get_emoji(873921151372513312)
        emojiNext = self.client.get_emoji(873921151716438016)
        emojiEnd = self.client.get_emoji(873921151280234537)
        btnStart = Button(style=ButtonStyle.gray, emoji = emojiStart, id = 'start')
        btnPrevious = Button(style=ButtonStyle.gray, emoji = emojiPrevious, id = 'previuos')
        btnNext = Button(style=ButtonStyle.gray, emoji = emojiNext, id = 'next')
        btnEnd = Button(style=ButtonStyle.gray, emoji = emojiEnd, id = 'end')
        components=[[btnStart, btnPrevious, btnNext, btnEnd,]]
        sticker = ''
        title = ''

        if message.channel != channel:
            return

        queryList = ['> `{0}.` **｢{1}｣**\n> добавил(-a) ✎﹏{2}\n> _ _'.format(i + 1,
                                                        self.queryData[self.queryList[i]]['title'],
                                                        self.queryData[self.queryList[i]]['user'],
                                                        self.queryData[self.queryList[i]]['duration'],)
                                                    for i in range(0, len(self.queryList))]

        pages = [queryList[i:i+5] for i in range(0, len(queryList), 5)]
        page = 0


        if len(self.queryList) == 0 and not self.lastAudio:
            answer = 'Пусто('
            sticker = discord.File('files/photo/Emoji (33).png')

        else:
            title = '`Сейчас играет` — ｢{0}｣ `добавил(-a)` ✎﹏*{1}*'.format(self.queryData[self.lastAudio]['title'], self.queryData[self.lastAudio]['user'])
            description = '> \n{0}\n> ˗ˏˋ `Время проигрывания:` **｢03:00:36 ｣** ˎˊ˗ '.format('\n'.join(pages[page]),)


        print(111111111111111111111)
        if title:
            embed = createEmbed(title = title, description = description, color = 0xf08080)
            question = await channel.send(embed = embed, components = components)
            while True:
                def check(res):
                    return res.channel ==channel and res.author == message.author and res.message.id == question.id

                try:
                    res = await self.client.wait_for("button_click", check = check, timeout = 10.0)
                    print("УСПЕШНО ПОЛУЧИЛИ КНОПКУ")

                except:

                    print("ОШИБКА КНОПКИ")
                    await question.delete()

                else:
                    print("ЗАПОЛНЯЕМ КНОПКУ")
                    if res.component.id == 'start':
                        page = 0

                    elif res.component.id == 'previuos':
                        if page != 0:
                            page -= 1

                    elif res.component.id == 'next':
                        if page != len(pages) - 1:
                            page += 1

                    elif res.component.id == 'end':
                        page = len(pages) - 1
                    print("ИЗМЕНИЛИ СТРАНИЦУ")
                    description = '> \n{0}\n> ˗ˏˋ `Время проигрывания:` **｢03:00:36 ｣** ˎˊ˗ '.format('\n'.join(pages[page]),)
                    print("DISCRIPTION")

                    embed = createEmbed(title = title, description = description, color = 0xf08080)
                    print("СОЗДАЛИ НОВЫЙ ЕМБЕД")

                    print("ОТПРАВЛЯЕМ НОВОЕ")

                    await res.respond(type=7, embed = embed)#?????

        else:
            await channel.send(answer, file = sticker)


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

    async def getSpoti(self, URL, user, message):
        #channel = await self.client.fetch_channel(self.config['data'].getint('mpChannel'))

        if 'playlist' in URL:
            #mes = 'Начала добавлять плейлист, Нья!'
            #asyncio.run_coroutine_threadsafe(channel.send(mes), self.loop)
            #message = await channel.send(mes)
            playlistID = URL[34:56]

            res = []
            offset = 0
            playlist_info = self.sp.playlist_tracks(playlistID, offset=offset)
            while playlist_info['items']:
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
                offset += 100
                playlist_info = self.sp.playlist_tracks(playlistID, offset=offset)


            url = 'https://www.youtube.com/watch_videos?video_ids='
            await self.getYoutube([url + ','.join(res[i:i+50]) for i in range(0, len(res), 50)], user, message = message)
            #answer = 'Добавила плейлист в очередь, Нья!'
            #await message.edit(content = answer)
            #asyncio.run_coroutine_threadsafe(message.edit(content = answer), self.loop)


        else:
            trackID = URL[31:54]
            trackInfo = self.sp.track(trackID)
            track = trackInfo['album']['artists'][0]['name'] + ' ' + trackInfo['name']
            results = YoutubeSearch(track, max_results=1).to_dict()
            await self.getYoutube('https://www.youtube.com' + results[0]['url_suffix'], user, message = message)





    async def getYoutube(self, URL, user, message = None, question = None, description = None):


        answer = 'Добавила трек в очередь, Нья!'

        if 'list' in URL or 'watch_videos' in URL or type(URL) == list:
            answer = 'Добавила плейлист в очередь, Нья!'

        #ydl_opts = {'format': 'bestaudio'}

        ydl_opts = {
            'ignoreerrors': True,
            'audio-format': 'mp3',
            'yes-playlist': True,
        }
        if URL:

            with YoutubeDL(ydl_opts) as ydl:
                if type(URL) == list:
                    links = []
                    for urlik in URL:
                        info = ydl.extract_info(urlik, download=False)
                        for track in info['entries']:
                            links.append(track)

                    for track in links:
                        self.getData(track, user)
                else:
                    info = ydl.extract_info(URL, download=False)

            if type(URL) != list and ('list' in URL or 'video_ids' in URL):
                for track in info['entries']:
                    self.getData(track, user)

            elif type(URL) != list:
                self.getData(info, user)


        if message:
            asyncio.run_coroutine_threadsafe(message.edit(content = answer), self.loop)
        elif question:
            embed = createEmbed(title = 'Трек был выбран и добавлен в очередь, нья!',
                                description = description,
                                footer = 'По МСК ' + getCurrentTime(),
                                color = 0xf08080)
            asyncio.run_coroutine_threadsafe(question.edit(embed = embed), self.loop)



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
                self.vc.play(discord.FFmpegPCMAudio(self.queryData[self.lastAudio]['URL'], **FFMPEG_OPTIONS))#, executable = 'C:/FFMPEG/bin/ffmpeg.exe'))

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
        try:
            URL = info['formats'][0]['url']
            title = info['title']
            duration = info['duration']
            self.addTrack(title, URL, duration, user)
        except:
            print('Не получилось добавить трек - ', info)
