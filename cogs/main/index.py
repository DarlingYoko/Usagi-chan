import discord, pytz, copy
from discord.ext import commands, tasks
from twitchAPI.twitch import Twitch
from .utils import gen_pic
from datetime import datetime

class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.check_twitch_online.start()
        self.wordle_results.start()


    @commands.command()
    @commands.is_owner()
    async def purge(self, ctx, limit: int):
        await ctx.channel.purge(limit = limit + 1)
        await ctx.send('Успешно удалила', delete_after = 10)

    @commands.command()
    @commands.is_owner()
    async def send(self, ctx, channel_id: int, *, message: str):
        try:
            channel = await ctx.bot.fetch_channel(channel_id)
        except:
            guild = await ctx.bot.fetch_guild(self.config['data']['guild_id'])
            channel = guild.get_thread(channel_id)
        await channel.send(message)

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('Nothing to see here comrade.')
        else:
            print(error)

    @commands.command()
    @commands.is_owner()
    async def connect(self, ctx, channel_id: int):
        channel = await ctx.bot.fetch_channel(channel_id)
        await channel.connect()
        await ctx.send('Успешно подключилась')

    @connect.error
    async def connect_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('Nothing to see here comrade.')
        else:
            print(error)


    @commands.command(name = 'помощь', aliases = ['хелп', 'хлеп'])
    async def help(self, ctx, *, args = None):
        if args:
            await ctx.send_help(args)
        else:
            await ctx.send_help()

    @commands.command(name = 'redirect')
    @commands.is_owner()
    async def redirect(self, ctx, switch: str):
        if switch == 'on':
            self.bot.redirect = True
            answer = 'Включила переадресацию'
        elif switch == 'off':
            self.bot.redirect = False
            answer = 'Выключила переадресацию'
        await ctx.send(answer)

    @tasks.loop(minutes=1)
    async def check_twitch_online(self):
        users = self.bot.db.get_all('twitch')
        # status = twitch.get_streams(user_login=['yoko_o0', 'tunnelkin', 'stepustk', 'hyver', 'uselessmouth', 'kegebe88'])
        # print(users)
        channel = await self.bot.fetch_channel(858053937008214018)
        for user in users:
            name = user[0]
            time = user[1]
            status = self.bot.twitch.get_streams(user_login=[name])
            if status['data']:
                user = status['data'][0]
                new_time = user['started_at']
                if new_time != time:
                    text, file = gen_pic(user, self.bot.twitch)
                    await channel.send(text, file = file)
                    self.bot.db.update('twitch', 'time', 'username', new_time, name)

    @check_twitch_online.before_loop
    async def before_check_twitch_online(self):
        print('waiting check twitch online')
        await self.bot.wait_until_ready()




    @commands.command(name = 'stream_add')
    async def add_streamer(self, ctx, streamer: str):
        if streamer.lower() == 'nuke73':
            answer = 'Этот стример заблокирован за откровенный или чувствительный контент и удалён модератором. Подробные правила можно найти в <#858096576136347648>'
            return await ctx.send(answer)
        r = self.bot.db.insert('twitch', streamer, 0)
        answer = 'Не получилось добавить нового стримера('
        if r:
            answer = 'Добавила нового стримера!'
        await ctx.send(answer)

    @commands.command(name = 'stream_del')
    @commands.is_owner()
    async def del_streamer(self, ctx, streamer: str):
        r = self.bot.db.remove('twitch', 'username', streamer)
        answer = 'Не получилось удалить нового стримера('
        if r:
            answer = 'Удалила стримера!'
        await ctx.send(answer)

    @commands.command(name = 'stream_show')
    async def show_all_streamers(self, ctx):
        users = self.bot.db.get_all('twitch')
        answer = 'Сейчас нет добавленных стримеров.'
        if users:
            answer = 'Вот список стримеров:\n'
        for user in users:
            answer += f'{user[0]}\n'

        await ctx.send(answer)


    @tasks.loop(minutes=1)
    async def wordle_results(self):
        timezone = pytz.timezone("Europe/Moscow")
        time = datetime.now(timezone)
        if time.hour == 23 and time.minute == 0:
            # print('Testing')

        # self.bot.db.update('forum', 'time', 'userid', time, 2)
        #
        # self.bot.db.update('forum', 'time', 'userid', '933469504174981161', 2)
            message_id = self.bot.db.get_value('forum', 'time', 'userid', 2)
            # print(message_id)
            channel = await self.bot.fetch_channel(932628946443468841)
            message_after = discord.Object(id = message_id)
            top_ru = {
                '1/6': [],
                '2/6': [],
                '3/6': [],
                '4/6': [],
                '5/6': [],
                '6/6': [],
                'x/6': [],
            }
            top_eng = copy.deepcopy(top_ru)
            top_math = copy.deepcopy(top_ru)
            top_ru_day = ''
            top_eng_day = ''
            top_math_day = ''
            async for message in channel.history(after=message_after, limit=None):
                text = message.content.lower()
                # print(text)
                if 'wordle' in text:
                    text_split = text.split()
                    # print(message.author.name, text)
                    try:
                        if '(ru)' in text:
                            rating = text_split[text_split.index('wordle') + 4]
                            top_ru[rating].append(message.author.name)
                            top_ru_day = text_split[text_split.index('wordle') + 3]
                        else:
                            rating = text_split[text_split.index('wordle') + 2]
                            top_eng[rating].append(message.author.name)
                            top_eng_day = text_split[text_split.index('wordle') + 1]
                    except:
                        pass
                if 'mathler.com' in text:
                    text_split = text.split()
                    try:
                        rating = text_split[text_split.index('mathler.com') + 2]
                        top_math[rating].append(message.author.name)
                        top_math_day = text_split[text_split.index('mathler.com') + 1]
                    except:
                        pass

            # print(top_eng)
            # print(top_ru)
            answer = f'```cs\n# Wordle (RU) День {top_ru_day}\n'
            for key, value in top_ru.items():
                answer += key + ' ' + '; '.join(value) + '\n'
            answer += '```'
            await channel.send(answer)

            answer = f'```cs\n# Wordle (ENG) Day #{top_eng_day}\n'
            for key, value in top_eng.items():
                answer += key + ' ' + '; '.join(value) + '\n'
            answer += '```'

            answer = f'```cs\n# Math Wordle Day #{top_math_day}\n'
            for key, value in top_math.items():
                answer += key + ' ' + '; '.join(value) + '\n'
            answer += '```'

            message = await channel.send(answer)
            self.bot.db.update('forum', 'time', 'userid', message.id, 2)




    @wordle_results.before_loop
    async def before_wordle_results(self):
        print('waiting wordle results')
        await self.bot.wait_until_ready()






def setup(bot):
    bot.add_cog(Main(bot))
