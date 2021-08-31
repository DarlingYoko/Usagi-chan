import discord
from discord.ext import commands, tasks
from bin.functions import *
from bin.checks import *
from bin.converters import *
from datetime import datetime, timedelta
from time import mktime

config = get_config()


class Technical(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        #self.notify_forum_login.start()
        #self.countdown_for_update.start()
        #self.notify_transformator.start()
        self.db = self.bot.get_cog('Database')


    @commands.Cog.listener()
    async def on_ready(self):
        self.db = self.bot.get_cog('Database')


    @commands.command(name = 'эмодзи', brief='Добавление нового эмодзи', help = str(config['channel'].getint('emoji')))
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
                channel = await self.bot.fetch_channel(channel_id)
                await channel.send(message)

    @tasks.loop(minutes=10.0)
    async def notify_transformator(self):
        usersList = self.db.get_all(tableName = 'forum')
        for (userID, time) in usersList:
            if userID == 1:
                continue
            time = datetime.fromtimestamp(float(time))

            if datetime.now() - time >= timedelta(days = 6, hours = 22):
                channel = await self.bot.fetch_channel(config['channel'].getint('transformator'))
                await channel.send('<@{0}> Преобразователь готов, нья!'.format(userID))
                time = mktime(datetime.now().timetuple())
                self.db.update('forum', 'time', 'userid', time, userID)


    @commands.group(name = 'преобразователь', brief='Добавление/изменение преобразователя.', help = str(config['channel'].getint('transformator')))
    @is_channel(config['channel'].getint('transformator'))
    async def transformator(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('преобразователь')


    @transformator.command(name = 'добавить')
    async def transformator_add(self, ctx, time: int = None):
        request = f"SELECT EXISTS(SELECT * from forum where userid = {ctx.author.id});"
        user_in_db = self.db.custom_command(request)[0][0]

        if time:
            delta = 166 - time
            time = mktime((datetime.now() - timedelta(hours = delta)).timetuple())
        else:
            time = mktime(datetime.now().timetuple())

        if user_in_db:
            response = self.db.update('forum', 'time', 'userid', time, ctx.author.id)
            if response:
                answer = f'{ctx.author.mention} Успешно изменила, нья!'
        else:
            response = self.db.insert('forum', ctx.author.id, time)
            if response:
                answer = f'{ctx.author.mention} Успешно добавила, нья!'

        if not response:
            answer = f'{ctx.author.mention}  Не получилось тебя добавить, пластити!'

        await ctx.send(answer)


    @transformator_add.error
    async def transformator_add_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f'<@{ctx.author.id}> Ты ввёл неверное время! Баака')


    @transformator.command(name = 'удалить')
    async def transformator_remove(self, ctx):
        request = f"SELECT EXISTS(SELECT * from forum where userid = {ctx.author.id});"
        user_in_db = self.db.custom_command(request)[0][0]

        if user_in_db:
            response = self.db.remove('forum', 'userid', ctx.author.id)
            if response:
                answer = f'{ctx.author.mention} Успешно удалено, нья!'

            else:
                answer = f'{ctx.author.mention} Не получилось тебя удолить, пластити!'

        else:
            answer = f'{ctx.author.mention} тебя нет в базе, Бааака!'

        await ctx.send(answer)

    @tasks.loop(minutes=10.0)
    async def countdown_for_update(self):
        time = self.db.get_value('forum', 'time', 'userid', 1)
        if not time:
            return

        channel = await self.bot.fetch_channel(config['channel'].getint('time'))

        now = datetime.now()
        if not time:
            return
        time = datetime.fromtimestamp(float(time))
        d = time - now
        hours = d.seconds // 3600
        minutes = (d.seconds - (hours * 3600)) // 60

        daysStr = 'дней'
        if d.days == 1:
            daysStr = 'день'
        elif d.days >= 2 and d.days <= 4:
            daysStr = 'дня'

        hoursStr = 'часов'
        if hours % 10 == 1 and hours != 11:
            hoursStr = 'час'
        elif hours % 10 >= 2 and hours % 10 <= 4 and hours not in [12, 13, 14]:
            hoursStr = 'часа'

        await channel.edit(name = '{0} {3} {1} {4} {2} мин'.format(d.days, hours, minutes, daysStr, hoursStr))


    @commands.command(name = 'time')
    @commands.is_owner()
    async def set_countdown(self, ctx, *, new_time):

        time = datetime.strptime(new_time, '%d.%m.%y %H:%M')
        time = mktime(time.timetuple())
        self.db.update('forum', 'time', 'userid', time, 1)
        await ctx.send('Новое время утсановлено, нья!')

    @set_countdown.error
    async def set_countdown_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(f'{ctx.author.mention}, тебе низя использовать эту команду.')
        await ctx.send('Не получилось установить новое время')


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print(ctx.command.name)
        if isinstance(error, commands.CheckFailure) and 'преобразователь' in ctx.command.name:
            channel = config['channel'].getint('transformator')
            await ctx.send(f'{ctx.author.mention}, тебе низя использовать эту команду туть. Сюда <#{channel}>')



    @commands.group(name = 'роль', brief='Настройка роли.', description='Обязательно указывайте название роли в "" (двойных кавычках :AD:)', help = str(config['channel'].getint('create_role')))
    @is_channel(config['channel'].getint('create_role'))
    async def role_settings(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('роль')


    @role_settings.command(name = 'добавить', help = str(config['channel'].getint('create_role')))
    async def create_new_role(self, ctx, name, color: ColorConverter):
        role = await ctx.guild.create_role(name = name, colour = color, hoist = True, mentionable = True)
        await ctx.author.add_roles(role)
        await ctx.send(f'{ctx.author.mention} Создала новую роль')

    @role_settings.command(name = 'удалить')
    async def remove_role(self, ctx, role: RoleConverter):
        await role.delete()
        await ctx.send(f'{ctx.author.mention}, Изменила название')

    @role_settings.group(name = 'изменить')
    async def change_role(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f'{ctx.author.mention}, ты не указал что мне надо сделать, Баааака!')

    @change_role.command(name = 'название')
    async def change_role_name(self, ctx, role: RoleConverter, name):
        await role.edit(name = name)
        await ctx.send(f'{ctx.author.mention}, Изменила название')

    @change_role.command(name = 'цвет')
    async def change_role_color(self, ctx, role: RoleConverter, color: ColorConverter):
        await role.edit(colour = color)
        await ctx.send(f'{ctx.author.mention}, Изменила цвет')


    @role_settings.error
    async def role_settings_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            channel = config['channel'].getint('create_role')
            await ctx.send(f'{ctx.author.mention}, тебе низя использовать эту команду туть. Сюда <#{channel}>')

        if isinstance(error, commands.BadArgument):
            await ctx.send(f'{ctx.author.mention}, ты ввёл неправильные аргументы, бааака!')

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.mention}, ты ничего не ввёл, бааака!')





def setup(bot):
    bot.add_cog(Technical(bot))

'''
!роль добавить "название" "цвет"
!роль удалить "ID роли"
!роль изменить "ID роли" "что надо изменить название/цвет" "новое название/цвет"
'''
