import discord
import spotipy, asyncio, re, itertools, random
import spotipy.oauth2 as oauth2
from discord.ext import commands, tasks
from bin.functions import *
from bin.checks import *
from cogs.music.extra import *
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from youtube_search import YoutubeSearch
from threading import Thread
from datetime import timedelta

class Music_Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.play_url.start()

        self.config = bot.config

        self.vc = None
        self.repeat = None
        self.pause = None
        self.queryList = []
        self.queryData = {}
        self.lastAudio = None
        self.counter = itertools.count()

        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        CLIENT_ID = '118b5bcd3192449282a6618c19f70d50'
        CLIENT_SECRET = '6d3496fc16f54a1586036c06a813894a'

        auth_manager = SpotifyClientCredentials(client_id = CLIENT_ID,
                                                client_secret = CLIENT_SECRET)


        self.sp = spotipy.Spotify(auth_manager = auth_manager)


    @commands.command(
        aliases = ['p'],
        usage = '<URL>|text for search',
        help = 'mp',
        description = 'Добавить трек/лист в очередь'
    )
    @commands.check(is_mp_channel)
    @commands.check(is_user_in_voice)
    async def play(self, ctx, *, URL: str):

        vc = get_vc(self)

        if not vc:
            channel = await self.bot.fetch_channel(self.config['channel']['mp_voice'])
            main = self.bot.get_cog('Main')
            await ctx.invoke(main.connect, channel_id = channel.id)

        channel = ctx.channel
        user_name = ctx.author.display_name.split('#')[0]
        answer = 'Не получилось добавить трек в очередь( Пипакрай'

        mes = 'Начала добавлять трек, Нья!'
        regexYouTube = 'http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)?'
        regexSpoti = 'spotify'

        if 'list' in URL:
            mes = 'Начала добавлять плейлист, Нья!'

        elif 'album' in URL:
            mes = 'Начала добавлять альбом, Нья!'

        if re.search(regexYouTube, URL):
            message = await channel.send(mes)
            Thread(target = asyncio.run, args=(self.get_youtube(URL, user_name, message ), )).start()
            answer = ''

        elif re.search(regexSpoti, URL):
            message = await channel.send(mes)
            Thread(target = asyncio.run, args=(self.get_spoti(URL, user_name, message), )).start()
            answer = ''


        else:
            async with ctx.typing():
                title = 'Выбор трека'
                trackID = -1
                results = YoutubeSearch(URL, max_results=5).to_dict()
                description = '\n\n'.join(['{0}. {1} **[{2}]**'.format(i+1, results[i]['title'], results[i]['duration']) for i in range(5)])
                embed = get_embed(title = title, description = description, color = 0xf08080)

                components = get_search_btns(ctx)

                question = await ctx.send(embed = embed, components = components)

            def check(res):
                return res.channel == channel and res.author == ctx.author and res.message.id == question.id

            try:
                res = await ctx.bot.wait_for("button_click", check = check, timeout = 60.0)

            except:
                title = 'Ты не выбрал трек за отведённое время, бака!'
                description = 'Бака бааака!'

            else:
                trackID = int(res.component.id)
                title = 'Трек под номером {} добавляется в очередь, Нья!'.format(trackID + 1)
                description = '{0} **[{1}]**'.format(results[trackID]['title'], results[trackID]['duration'])



            answer = ''
            embed = get_embed(title = title, description = description, color = 0xe00000)
            await question.edit(embed = embed, components = [])

            if trackID != -1:
                URL = 'https://www.youtube.com' + results[trackID]['url_suffix']
                Thread(target = asyncio.run, args=(self.get_youtube(URL, user_name, question, embed = embed), )).start()

        if answer:
            await ctx.send(answer)


    @play.error
    async def not_found_user(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Неверный запрос')

        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(str(error))



    @commands.command(
        aliases=['пауза'],
        help = 'mp',
        description = 'Поставить на паузу'
    )
    @commands.check(is_mp_channel)
    @commands.check(is_user_in_voice)
    async def pause(self, ctx):
        vc = get_vc(self)
        answer = 'Я не нахожусь в войсе, бака!'
        if vc:
            answer = 'Поставила на паузу, Нья!!'
            vc.pause()

        await ctx.send(answer)


    @commands.command(
        help = 'mp',
        description = 'Продолжить играть'
    )
    @commands.check(is_mp_channel)
    @commands.check(is_user_in_voice)
    async def resume(self, ctx):
        vc = get_vc(self)
        answer = 'Я не нахожусь в войсе, бака!'
        if vc:
            answer = 'Продолжаю играть, Нья!!'
            vc.resume()

        await ctx.send(answer)

    @commands.command(
        help = 'mp',
        description = 'Остановить и очистить очередь'
    )
    @commands.check(is_mp_channel)
    @commands.check(is_user_in_voice)
    async def stop(self, ctx):
        vc = get_vc(self)

        if not vc:
            channel = await self.bot.fetch_channel(self.config['channel']['mp_voice'])
            main = self.bot.get_cog('Main')
            await ctx.invoke(main.connect, channel_id = channel.id)

        await ctx.message.add_reaction(self.emojiGreenTick)
        await ctx.message.add_reaction(self.emojiRedTick)
        await asyncio.sleep(10)

        reacts = ctx.message.reactions

        vote = await self.get_vote_result(reacts, vc)

        if vote:
            vc.stop()
            self.repeat = None
            self.queryList = []
            self.queryData = {}
            self.lastAudio = None
            answer = 'Остановила и очистила, Нья!'

        else:
            answer = 'Большинство проголосовало против стопа, Нья!'

        await ctx.send(answer)

    @commands.command(
        aliases = ['s'],
        help = 'mp',
        description = 'Скипнуть треки/трек',
        usage = '<ничего если текущий>|<1,2,3>|<1-4>'
        )
    @commands.check(is_mp_channel)
    @commands.check(is_user_in_voice)
    async def skip(self, ctx, *, arg = None):
        vc = get_vc(self)

        if not vc:
            channel = await self.bot.fetch_channel(self.config['channel']['mp_voice'])
            main = self.bot.get_cog('Main')
            await ctx.invoke(main.connect, channel_id = channel.id)

        await ctx.message.add_reaction(self.emojiGreenTick)
        await ctx.message.add_reaction(self.emojiRedTick)
        await asyncio.sleep(10)

        reacts = ctx.message.reactions

        vote = await self.get_vote_result(reacts, vc)

        if vote:
            if arg and '-' in arg:
                try:
                    content = arg.split('-')
                    start = int(content[0].strip())
                    end = int(content[1].strip())
                except IndexError:
                    answer = 'Не получилось скипнуть, проверь команду, бака!'
                else:
                    for i in range(start - 1, end):
                        del self.queryData[self.queryList.pop(start - 1)]

                    answer = 'Песни скипнуты'

            elif arg:
                try:
                    content = [int(i.strip()) - 1 for i in arg.split(',')]
                    content.sort()
                    for i in range(len(content)):
                        del self.queryData[self.queryList.pop(content[i] - i)]

                except IndexError:
                    answer = 'Не получилось скипнуть, проверь команду, бака!'
                else:
                    answer = 'Песни скипнуты'
            else:
                if len(self.queryList) > 0:
                    vc.stop()
                    answer = 'Песни скипнуты'
                else:
                    vc.stop()
                    answer = 'Больше песенок нет('
                    self.lastAudio = None

        else:
            answer = 'Большинство проголосовало против скипа, Нья!'

        if answer:
            await ctx.send(answer)

    @commands.command(
        aliases = ['q'],
        help = 'mp',
        description = 'Показать очередь'
    )
    @commands.check(is_mp_channel)
    async def query(self, ctx):

        sticker = ''
        title = ''

        queryList = ['> `{0}.` **｢{1}｣**\n> added by ✎﹏{2}\n> _ _'.format(i + 1,
                                                        self.queryData[self.queryList[i]]['title'],
                                                        self.queryData[self.queryList[i]]['user'],
                                                        self.queryData[self.queryList[i]]['duration'],)
                                                    for i in range(0, len(self.queryList))]

        pages = [queryList[i:i+5] for i in range(0, len(queryList), 5)]
        page = 0


        duration = self.get_duration()
        components = get_query_btns(ctx, f'Page {page + 1}/{len(pages)}')


        if len(self.queryList) == 0 and not self.lastAudio:
            answer = 'Empty('
            sticker = discord.File('files/photo/Emoji (33).png')

        else:
            if self.lastAudio:
                title = '`Now playing` — ｢{0}｣ `added by` ✎﹏*{1}*'.format(self.queryData[self.lastAudio]['title'], self.queryData[self.lastAudio]['user'])
            else:
                title = 'Сейчас ничего не играет'

            if pages:
                description = '> \n{0}\n> ˗ˏˋ `Playing time:` **｢{1} ｣** ˎˊ˗ \n'.format('\n'.join(pages[page]), duration)
            else:
                description = ''

        if title:
            async with ctx.typing():
                embed = get_embed(title = title, description = description, color = 0xf08080)
                question = await ctx.send(embed = embed, components = components)

            while True:
                def check(res):
                    return res.channel == ctx.channel and res.author == ctx.author and res.message.id == question.id

                try:
                    res = await self.bot.wait_for("button_click", check = check, timeout = 60.0)

                except:
                    await question.delete()
                    await ctx.message.delete()
                    return

                else:
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
                    description = '> \n{0}\n> ˗ˏˋ `Playing time:` **｢{1} ｣** ˎˊ˗ \n'.format('\n'.join(pages[page]), duration)

                    embed = get_embed(embed = embed, description = description, color = 0xf08080)
                    components = get_query_btns(ctx, f'Page {page + 1}/{len(pages)}')
                    await res.respond(type=7, embed = embed, components = components)

        else:
            await ctx.send(answer, file = sticker)

    @commands.command(
        aliases = ['sh'],
        help = 'mp',
        description = 'Перемешать очередь')
    @commands.check(is_mp_channel)
    @commands.check(is_user_in_voice)
    async def shuffle(self, ctx):
        answer = 'Очередь пуста, Бааака!'
        if self.queryList:
            random.shuffle(self.queryList)
            answer = 'Перемешала очередь, Нья!!'
        await ctx.send(answer)

    @commands.command(
        aliases = ['репит'],
        help = 'mp',
        description = 'Поставить на репит, пока только сингл',
        usage = '<last|no>'
    )
    @commands.check(is_mp_channel)
    @commands.check(is_user_in_voice)
    async def repeat(self, ctx, arg: str):
        if arg.lower() == 'last':
            self.repeat = True
            answer = 'Трек на репите, Нья!!'
        elif arg.lower() == 'no':
            self.repeat = False
            answer = 'Репит отключен, Нья!!'
        else:
            raise commands.BadArgument
        await ctx.send(answer)

    @repeat.error
    async def repeat_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            return await ctx.send('Такого я не могу')
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help('repeat')

    @commands.command(
        aliases = ['np'],
        help = 'mp',
        description = 'Посмотреть текущий трек'
    )
    @commands.check(is_mp_channel)
    async def now_play(self, ctx):
        answer = 'Ничего не играет'

        if self.lastAudio:
            duration = self.get_duration(target = self.queryData[self.lastAudio])
            name = self.queryData[self.lastAudio]['title']
            user_name = self.queryData[self.lastAudio]['user']
            answer = f'Now playing — **｢{name}｣** added by **{user_name}** `{duration}`'

        await ctx.send(answer)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        music_commands = ['play', 'pause', 'resume', 'stop', 'skip', 'query', 'shuffle']
        if isinstance(error, commands.CheckFailure) and ctx.command.name in music_commands:
            channel = self.config['channel']['mp']
            voice = self.config['channel'].getint('mp_voice')
            await ctx.send(f'Низя использовать эту команду туть. Тебе сюда <#{channel}> и подключись к войсу <#{voice}>')


    @tasks.loop(seconds=5.0)
    async def play_url(self):
        vc = get_vc(self)

        if not vc:
            return

        if not vc.is_playing() and not vc.is_paused():
            URL = ''
            if self.repeat and self.lastAudio:
                URL = get_info_by_URL(self.queryData[self.lastAudio]['URL'])

            elif len(self.queryList) > 0:
                if self.lastAudio:
                    del self.queryData[self.lastAudio]
                self.lastAudio = self.queryList.pop(0)
                URL = get_info_by_URL(self.queryData[self.lastAudio]['URL'])

            elif len(self.queryList) == 0:
                if self.lastAudio:
                    del self.queryData[self.lastAudio]
                    self.lastAudio = None

            if URL:
                channel = await self.bot.fetch_channel(self.config['channel']['mp'])
                print('URL FOR PLAYING - ', URL['formats'][0]['url'])
                vc.play(discord.FFmpegPCMAudio(URL['formats'][0]['url'], **self.FFMPEG_OPTIONS))#, executable = 'C:/FFMPEG/bin/ffmpeg.exe'))

                duration = self.get_duration(target=self.queryData[self.lastAudio])
                name = self.queryData[self.lastAudio]['title']
                user_name = self.queryData[self.lastAudio]['user']
                answer = f'Start play — **｢{name}｣** added by **{user_name}** `{duration}`'

                await channel.send(answer)
                print('начинаю играть')

    @play_url.before_loop
    async def before_play_url(self):
        print('waiting music')
        await self.bot.wait_until_ready()
        self.loop = asyncio.get_event_loop()
        self.emojiGreenTick = self.bot.get_emoji(874767321007276143)
        self.emojiRedTick = self.bot.get_emoji(874767320915005471)


    async def get_youtube(self, URL, user_name, question, embed = None):

        answer = 'Добавила трек в очередь, Нья!'

        if 'list' in URL or 'watch_videos' in URL:
            answer = 'Добавила плейлист в очередь, Нья!'

        info = get_info_by_URL(URL)
        if info:
            if 'entries' in info.keys():
                for track in info['entries']:
                    add_track(self, track, user_name)
            else:
                add_track(self, info, user_name)
        else:
            answer = 'Не удалось добавить трек'


        if embed:
            embed = get_embed(embed = embed, title = 'Трек был выбран и добавлен в очередь, нья!')
            asyncio.run_coroutine_threadsafe(question.edit(embed = embed), self.loop)

        else:
            asyncio.run_coroutine_threadsafe(question.edit(content = answer), self.loop)


    async def get_spoti(self, URL, user_name, question):
        #channel = await self.client.fetch_channel(self.self.config['data'].getint('mpChannel'))

        answer = 'Добавила трек в очередь, Нья!'

        if 'list' in URL:
            answer = 'Добавила плейлист в очередь, Нья!'

        elif 'album' in URL:
            mes = 'Добавила альбом в очередь, Нья!'

        if 'playlist' in URL or 'album' in URL:

            func = self.sp.playlist_tracks

            if 'album' in URL:
                func = self.sp.album_tracks

            try:
                playlistID = URL.split('/')[4].split('?')[0]
            except:
                printError()
                asyncio.run_coroutine_threadsafe(message.edit(content = 'Не получилось добавить('), self.loop)
                return
            # https://open.spotify.com/album/3oIFxDIo2fwuk4lwCmFZCx?si=20ebd7c4d1bf40d4 album
            # https://open.spotify.com/playlist/5j11jguZ5azMB1M8Xn0xvs?si=1cdddd2d85774dc0 playlist
            # https://open.spotify.com/track/3R1bUwe5mTclpush3T5P0a?si=df7822d1be3f4eb9 single

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
                        results[0]['duration'] = get_sec(results[0]['duration'])
                        print(results)
                        res.append(results[0])
                    except Exception as e:
                        printError()

                offset += 100
                playlist_info = func(playlistID, offset=offset)


            for track in res:
                add_track(self, track, user_name)



        else:
            trackID = URL.split('/')[4].split('?')[0]
            trackInfo = self.sp.track(trackID)
            track = trackInfo['album']['artists'][0]['name'] + ' ' + trackInfo['name']
            results = YoutubeSearch(track, max_results=1).to_dict()
            results[0]['duration'] = get_sec(results[0]['duration'])
            add_track(self, results[0], user_name)

        asyncio.run_coroutine_threadsafe(question.edit(content = answer), self.loop)

    def get_vc(self):
        vc = None
        for voice_client in self.bot.voice_clients:
            if voice_client.channel.id == self.config['channel'].getint('mp_voice'):
                vc = voice_client
        return vc

    def get_users_in_voice(self, users, vc):
        counter = 0
        for user in users:
            if user in vc.channel.members:
                counter += 1

        return counter

    async def get_vote_result(self, reacts, vc):
        greenReactCount = 0
        redReactCount = 0
        for react in reacts:
            if str(react) == str(self.emojiGreenTick):
                users = await react.users().flatten()
                greenReactCount = self.get_users_in_voice(users, vc)

            if str(react) == str(self.emojiRedTick):
                users = await react.users().flatten()
                redReactCount = self.get_users_in_voice(users, vc)

        if greenReactCount > redReactCount:
            return 1
        return 0

    def get_duration(self, target = None):
        time = 0
        if not target:
            for track in self.queryData.values():
                time += int(track['duration'])
        else:
            time = target['duration']
        return str(timedelta(seconds=time))

def setup(bot):
    bot.add_cog(Music_Player(bot))
