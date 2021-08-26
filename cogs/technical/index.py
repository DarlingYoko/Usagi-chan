import discord
from discord.ext import commands, tasks
from bin.functions import get_config
from bin.checks import *
from datetime import datetime, timedelta

config = get_config()


class Technical(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notify_forum_login.start()
        #self.notify_transformator.start()
        self.db = self.bot.get_cog('Database')


    @commands.Cog.listener()
    async def on_ready(self):
        self.db = self.bot.get_cog('Database')


    @commands.command(name = 'эмодзи', brief='Добавление нового эмодзи')
    @is_channel(config['channel'].getint('emoji'))
    async def create_new_emoji(self, ctx, name: str):

        if not ctx.message.attachments:
            raise commands.BadArgument

        image = None

        for attachment in ctx.message.attachments:
            if check_str_in_list(attachment.content_type, ['jpg', 'png', 'gif', 'jpeg']):
                image = await attachment.read()

        if not image:
            raise commands.BadArgument

        try:
            emoji = await ctx.guild.create_custom_emoji(name = name, image = image)
            await ctx.send(f'{ctx.author.mention} Успешно добавила, Нья! {emoji}')
        except Exception as e:
            await ctx.send(f'{ctx.author.mention} Не получилось добавить(\n{str(e)}')

    @create_new_emoji.error
    async def create_new_emoji_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f'<@{ctx.author.id}> Ты не прикрепил картинку! Баака')

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'<@{ctx.author.id}> Ты не написал название эмодзи! Баака')

        if isinstance(error, commands.CheckFailure):
            channel = config['channel'].getint('emoji')
            await ctx.send(f'Низя использовать эту команду туть. Тебе сюда <#{channel}>')




    @tasks.loop(minutes=30.0)
    async def notify_forum_login(self):
        if datetime.now().hour == 16:
            message = 'Не забываем забрать логин бонус!\n<https://webstatic-sea.mihoyo.com/ys/event/signin-sea/index.html?act_id=e202102251931481&lang=ru-ru>'
            channels_id = [config['channel'].getint('main'), config['channel'].getint('bar')]
            for channel_id in channels_id:
                channel = await self.client.fetch_channel(channel_id)
                await channel.send(message)

    @tasks.loop(minutes=10.0)
    async def notify_transformator(self):
        usersList = self.db.get_all(tableName = 'forum')
        for (userID, time) in usersList:
            if userID == 1:
                continue
            time = datetime.fromtimestamp(float(time))

            if datetime.now() - time >= timedelta(days = 6, hours = 22):
                channel = await self.client.fetch_channel(config['channel'].getint('transformator'))
                await channel.send('<@{0}> Преобразователь готов, нья!'.format(userID))
                time = mktime(datetime.now().timetuple())
                self.db.update('forum', 'time', 'userid', time, userID)







def setup(bot):
    bot.add_cog(Technical(bot))
