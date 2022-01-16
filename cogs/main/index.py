import discord
from discord.ext import commands, tasks
from twitchAPI.twitch import Twitch
from .utils import gen_pic

class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.check_twitch_online.start()


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
        client_id = 'ytl8amzfrreo3hf413ywaua8jd7of8'
        client_secret = 'keiz535fdh87qb5a0h2to0vjz7ndi9'
        twitch = Twitch(client_id, client_secret)
        users = self.bot.db.get_all('twitch')
        # status = twitch.get_streams(user_login=['yoko_o0', 'tunnelkin', 'stepustk', 'hyver', 'uselessmouth', 'kegebe88'])
        print(users)
        channel = await self.bot.fetch_channel(858053937008214018)
        for user in users:
            name = user[0]
            time = user[1]
            status = twitch.get_streams(user_login=[name])
            if status['data']:
                user = status['data'][0]
                new_time = user['started_at']
                if new_time != time:
                    text, file = gen_pic(user, twitch)
                    await channel.send(text, file = file)
                    self.bot.db.update('twitch', 'time', 'username', new_time, name)

    @check_twitch_online.before_loop
    async def before_check_twitch_online(self):
        print('waiting...')
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





def setup(bot):
    bot.add_cog(Main(bot))
