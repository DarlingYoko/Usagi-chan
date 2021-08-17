import sys, discord, os, subprocess, random, time, asyncio, datetime, re
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

        self.emojiOne = self.client.get_emoji(873719561562755143)
        self.emojiTwo = self.client.get_emoji(873653970839674941)
        self.emojiThree = self.client.get_emoji(873653970751602719)
        self.emojiFour = self.client.get_emoji(873653970839670854)
        self.emojiFive = self.client.get_emoji(873653970994888704)

        self.emojiGreenTick = self.client.get_emoji(874767321007276143)
        self.emojiRedTick = self.client.get_emoji(874767320915005471)

        self.emojiStart = self.client.get_emoji(873921151896805487)
        self.emojiPrevious = self.client.get_emoji(873921151372513312)
        self.emojiNext = self.client.get_emoji(873921151716438016)
        self.emojiEnd = self.client.get_emoji(873921151280234537)

        self.loop = asyncio.get_running_loop()
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

        mes = 'Начала добавлять трек, Нья!'
        regexYouTube = 'http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?'
        regexSpoti = 'spotify'

        if 'list' in URL:
            mes = 'Начала добавлять плейлист, Нья!'

        elif 'album' in URL:
            mes = 'Начала добавлять альбом, Нья!'



        if re.search(regexYouTube, URL):
            message = await channel.send(mes)
            #await loop.run_in_executor(None, self.getYoutube(URL, user))
            #self.client.loop.create_task(self.getYoutube(URL, user))
            Thread(target = asyncio.run, args=(self.getYoutube(URL, user, message = message), )).start()
            answer = ''


        elif re.search(regexSpoti, URL):
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


            btn1 = Button(style=ButtonStyle.gray, emoji = self.emojiOne, id = '0')
            btn2 = Button(style=ButtonStyle.gray, emoji = self.emojiTwo, id = '1')
            btn3 = Button(style=ButtonStyle.gray, emoji = self.emojiThree, id = '2')
            btn4 = Button(style=ButtonStyle.gray, emoji = self.emojiFour, id = '3')
            btn5 = Button(style=ButtonStyle.gray, emoji = self.emojiFive, id = '4')
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
                title = 'Трек под номером {} добавляется в очередь, Нья!'.format(trackID + 1)
                description = '{0} **[{1}]**'.format(results[trackID]['title'], results[trackID]['duration'])



            answer = ''
            embed = createEmbed(title = title, description = description, footer = footer, color = 0xe00000)
            await question.edit(embed = embed, components = [])

            if trackID != -1:
                URL = 'https://www.youtube.com' + results[trackID]['url_suffix']
                Thread(target = asyncio.run, args=(self.getYoutube(URL, user, question = question, description = description), )).start()

        await channel.send(answer)


    def pauseAudio(self):
        self.vc.pause()
        self.pause = True

    def resume(self):
        self.vc.resume()
        self.pause = False

    async def stop(self, message):
        await message.add_reaction(self.emojiGreenTick)
        await message.add_reaction(self.emojiRedTick)
        await asyncio.sleep(20)

        reacts = message.reactions

        for react in reacts:
            #print(react, str(react), str(self.emojiGreenTick), str(self.emojiRedTick))
            if str(react) == str(self.emojiGreenTick):
                greenReactCount = react.count

            if str(react) == str(self.emojiRedTick):
                redReactCount = react.count

        if greenReactCount > redReactCount:
            self.vc.stop()
            self.repeat = None
            self.queryList = []
            self.lastAudio = None
            answer = 'Остановила и очистила, Нья!'

        else:
            answer = 'Большинство проголосовало против стопа, Нья!'

        await message.channel.send(answer)

    def shuffle(self):
        random.shuffle(self.queryList)

    def nowPlay(self):
        answer = 'Ничего не играет'
        duration = self.getDuration(target = self.queryData[self.lastAudio])
        if self.lastAudio:
            answer = 'Now playing - **{0}**, added by **{1}** `{2}`'.format(self.queryData[self.lastAudio]['title'],
                                                                                self.queryData[self.lastAudio]['user'],
                                                                                duration)
        return answer

    async def skip(self, message):
        content = message.content.strip().split('!s')[1]

        await message.add_reaction(self.emojiGreenTick)
        await message.add_reaction(self.emojiRedTick)
        await asyncio.sleep(20)

        reacts = message.reactions

        for react in reacts:
            #print(react, str(react), str(self.emojiGreenTick), str(self.emojiRedTick))
            if str(react) == str(self.emojiGreenTick):
                greenReactCount = react.count

            if str(react) == str(self.emojiRedTick):
                redReactCount = react.count

        if greenReactCount > redReactCount:
            if '-' in content:
                try:
                    content = content.split('-')
                    start = int(content[0])
                    end = int(content[1])
                except IndexError:
                    answer = 'Не получилось скипнуть, проверь команду, бака!'
                else:
                    for i in range(start - 1, end):
                        del self.queryData[self.queryList.pop(start - 1)]

                    answer = 'Песни скипнуты'

            elif content:
                try:
                    content = [int(i) - 1 for i in content.split(',')]
                    content.sort()
                    for i in range(len(content)):
                        del self.queryData[self.queryList.pop(content[i] - i)]


                except IndexError:
                    answer = 'Не получилось скипнуть, проверь команду, бака!'
                else:
                    answer = 'Песни скипнуты'
            else:
                if len(self.queryList) > 0:
                    self.vc.stop()
                    duration = self.getDuration(target = self.queryData[self.queryList[0]])
                    answer = 'Песенка скипнута\nNow playing - **{0}**, added by **{1}** `{2}`'.format(self.queryData[self.queryList[0]]['title'],
                                                                                                            self.queryData[self.queryList[0]]['user'],
                                                                                                            duration,)
                else:
                    self.vc.stop()
                    answer = 'Больше песенок нет('
                    self.lastAudio = None

        else:
            answer = 'Большинство проголосовало против скипа, Нья!'

        await message.channel.send(answer)

    async def query(self, message):

        channel = await self.client.fetch_channel(self.config['data'].getint('mpChannel'))


        btnStart = Button(style=ButtonStyle.gray, emoji = self.emojiStart, id = 'start')
        btnPrevious = Button(style=ButtonStyle.gray, emoji = self.emojiPrevious, id = 'previuos')
        btnNext = Button(style=ButtonStyle.gray, emoji = self.emojiNext, id = 'next')
        btnEnd = Button(style=ButtonStyle.gray, emoji = self.emojiEnd, id = 'end')
        components=[[btnStart, btnPrevious, btnNext, btnEnd,]]
        sticker = ''
        title = ''

        if message.channel != channel:
            return

        queryList = ['> `{0}.` **｢{1}｣**\n> added by ✎﹏{2}\n> _ _'.format(i + 1,
                                                        self.queryData[self.queryList[i]]['title'],
                                                        self.queryData[self.queryList[i]]['user'],
                                                        self.queryData[self.queryList[i]]['duration'],)
                                                    for i in range(0, len(self.queryList))]

        pages = [queryList[i:i+5] for i in range(0, len(queryList), 5)]
        page = 0


        duration = self.getDuration()



        if len(self.queryList) == 0 and not self.lastAudio:
            answer = 'Empty('
            sticker = discord.File('files/photo/Emoji (33).png')

        else:
            title = '`Now playing` — ｢{0}｣ `added by` ✎﹏*{1}*'.format(self.queryData[self.lastAudio]['title'],
                                                                                self.queryData[self.lastAudio]['user']
                                                                                )

            if pages:
                description = '> \n{0}\n> ˗ˏˋ `Playing time:` **｢{3} ｣** ˎˊ˗ \n*|Page {1} of {2}|*'.format('\n'.join(pages[page]),
                                                                                                                    page + 1,
                                                                                                                    len(pages),
                                                                                                                    duration
                                                                                                                    )
            else:
                description = ''


        print(111111111111111111111)
        if title:
            embed = createEmbed(title = title, description = description, color = 0xf08080)
            question = await channel.send(embed = embed, components = components)
            while True:
                def check(res):
                    return res.channel ==channel and res.author == message.author and res.message.id == question.id

                try:
                    res = await self.client.wait_for("button_click", check = check, timeout = 60.0)
                    print("УСПЕШНО ПОЛУЧИЛИ КНОПКУ")

                except:

                    print("ОШИБКА КНОПКИ")
                    await question.delete()
                    await message.delete()

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
                    description = '> \n{0}\n> ˗ˏˋ `Playing time:` **｢{3} ｣** ˎˊ˗ \n*|Page {1} of {2}|*'.format('\n'.join(pages[page]),
                                                                                                                                page + 1,
                                                                                                                                len(pages),
                                                                                                                                duration
                                                                                                                                )
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

        if 'playlist' in URL or 'album' in URL:
            #mes = 'Начала добавлять плейлист, Нья!'
            #asyncio.run_coroutine_threadsafe(channel.send(mes), self.loop)
            #message = await channel.send(mes)

            func = self.sp.playlist_tracks

            if 'album' in URL:
                func = self.sp.album_tracks

            try:
                playlistID = URL.split('/')[4].split('?')[0]
            except:
                print('Error in getting ID from spoti')
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print('New error:\ntype - {0}, line - {1}, error - {2}, file - {3}\n'.format(exc_type, exc_tb.tb_lineno, exc_obj, fname))
                asyncio.run_coroutine_threadsafe(message.edit(content = 'Не получилось добавить('), self.loop)
                return
            #https://open.spotify.com/album/3oIFxDIo2fwuk4lwCmFZCx?si=20ebd7c4d1bf40d4 album
            #https://open.spotify.com/playlist/5j11jguZ5azMB1M8Xn0xvs?si=1cdddd2d85774dc0 playlist

            res = []
            offset = 0
            playlist_info = func(playlistID, offset=offset)
            while playlist_info['items']:
                for track in playlist_info['items']:
                    try:
                        trackName = ''
                        if 'playlist' in URL:
                            if track['track']['id']:
                                trackInfo = self.sp.track(track['track']['id'])
                                trackName = trackInfo['album']['artists'][0]['name'] + ' ' + trackInfo['name']
                            else:
                                trackName = track['track']['name']
                        if 'album' in URL:
                            trackName = track['artists'][0]['name'] + ' ' + track['name']
                        results = YoutubeSearch(trackName, max_results=1).to_dict()
                        print(results)
                        res.append(results[0]['url_suffix'].split('/watch?v=')[1])
                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        print('New error:\ntype - {0}, line - {1}, error - {2}, file - {3}\n'.format(exc_type, exc_tb.tb_lineno, exc_obj, fname))
                        print('Error in adding url from spoti track')

                offset += 100
                playlist_info = func(playlistID, offset=offset)


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
            'verbose': True,
        }
        try:
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

                if type(URL) != list and 'entries' in info.keys():
                    for track in info['entries']:
                        self.getData(track, user)

                elif type(URL) != list:
                    self.getData(info, user)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('New error:\ntype - {0}, line - {1}, error - {2}, file - {3}\n'.format(exc_type, exc_tb.tb_lineno, exc_obj, fname))
            asyncio.run_coroutine_threadsafe(message.edit(content = 'Не получилось добавить('), self.loop)

        else:
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
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('New error:\ntype - {0}, line - {1}, error - {2}, file - {3}\n'.format(exc_type, exc_tb.tb_lineno, exc_obj, fname))

    def getDuration(self, target = None):
        time = 0
        if not target:
            for track in self.queryData.values():
                time += int(track['duration'])
        else:
            time = target['duration']
        return str(datetime.timedelta(seconds=time))
