import discord
from discord.ext import commands, tasks
from bin.functions import *
from bin.checks import *
from bin.converters import *
from datetime import datetime, timedelta
from time import mktime


class Technical(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.config = bot.config

        self.notify_forum_login.start()
        self.countdown_for_update.start()
        self.notify_transformator.start()




    @commands.command(
        name = 'эмодзи',
        brief='Добавление нового эмодзи',
        help = 'emoji',
        usage = '<название эмодзи> <прикрепить картинку или гифку>',
        description = 'Добавление новой эмодзи',

    )
    @commands.check(is_emoji_channel)
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
            channel = self.config['channel']['emoji']
            await ctx.send(f'Низя использовать эту команду туть. Тебе сюда <#{channel}>')




    @tasks.loop(minutes=30.0)
    async def notify_forum_login(self):
        if datetime.now().hour == 16:
            message = 'Не забываем забрать логин бонус!\n<https://webstatic-sea.mihoyo.com/ys/event/signin-sea/index.html?act_id=e202102251931481&lang=ru-ru>\nИли ты можешь подписаться на автоматический сбор дейли отметок -> `!help drs`'
            channels_id = [self.config['channel'].getint('main'), self.config['channel'].getint('bar')]
            for channel_id in channels_id:
                channel = await self.bot.fetch_channel(channel_id)
                await channel.send(message)

    @notify_forum_login.before_loop
    async def before_notify_forum_login(self):
        print('waiting for notify forum')
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=10.0)
    async def notify_transformator(self):
        usersList = self.bot.db.get_all(tableName = 'forum')
        for (userID, time) in usersList:
            if userID in [1, 2]:
                continue
            time = datetime.fromtimestamp(float(time))

            if datetime.now() - time >= timedelta(days = 6, hours = 22):
                channel = await self.bot.fetch_channel(self.config['channel'].getint('transformator'))
                await channel.send('<@{0}> Преобразователь готов, нья!'.format(userID))
                time = mktime(datetime.now().timetuple())
                self.bot.db.update('forum', 'time', 'userid', time, userID)

    @notify_transformator.before_loop
    async def before_notify_transformator(self):
        print('waiting for notify transformator')
        await self.bot.wait_until_ready()


    @commands.group(
        name = 'преобразователь',
        brief='Добавление/изменение преобразователя.',
        help = 'transformator',
        description = 'Настройка преобразователя',
    )
    @commands.check(is_transformator_channel)
    async def transformator(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('преобразователь')


    @transformator.command(
        name = 'добавить',
        usage = '<сколько времени до оповещения или пусто, если только что>',
        description = 'Добавление вашего преобразователя',
    )
    async def transformator_add(self, ctx, time: int = None):
        request = f"SELECT EXISTS(SELECT * from forum where userid = {ctx.author.id});"
        user_in_db = self.bot.db.custom_command(request)[0][0]

        if time and time < 0:
            raise commands.BadArgument

        if time:
            delta = 166 - time
            time = mktime((datetime.now() - timedelta(hours = delta)).timetuple())
        else:
            time = mktime(datetime.now().timetuple())

        if user_in_db:
            response = self.bot.db.update('forum', 'time', 'userid', time, ctx.author.id)
        else:
            response = self.bot.db.insert('forum', ctx.author.id, time)


        if response:
            answer = f'{ctx.author.mention} Успешно добавила, нья!'
        elif response and user_in_db:
            answer = f'{ctx.author.mention} Успешно обновила, нья!'
        else:
            answer = f'{ctx.author.mention}  Не получилось тебя добавить, пластити!'

        await ctx.send(answer)


    @transformator_add.error
    async def transformator_add_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f'<@{ctx.author.id}> Ты ввёл неверное время! Баака')


    @transformator.command(
        name = 'удалить',
        usage = '',
        description = 'Удаление вашего преобразователя',
    )
    async def transformator_remove(self, ctx):
        request = f"SELECT EXISTS(SELECT * from forum where userid = {ctx.author.id});"
        user_in_db = self.bot.db.custom_command(request)[0][0]

        if user_in_db:
            response = self.bot.db.remove('forum', 'userid', ctx.author.id)
            if response:
                answer = f'{ctx.author.mention} Успешно удалено, нья!'

            else:
                answer = f'{ctx.author.mention} Не получилось тебя удолить, пластити!'

        else:
            answer = f'{ctx.author.mention} тебя нет в базе, Бааака!'

        await ctx.send(answer)

    @tasks.loop(minutes=10.0)
    async def countdown_for_update(self):
        time = self.bot.db.get_value('forum', 'time', 'userid', 1)
        if not time:
            return

        channel = await self.bot.fetch_channel(self.config['channel'].getint('time'))

        now = datetime.now()
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

    @countdown_for_update.before_loop
    async def before_countdown_for_update(self):
        print('waiting for countdown update')
        await self.bot.wait_until_ready()


    @commands.command(name = 'time')
    @commands.is_owner()
    async def set_countdown(self, ctx, *, new_time):

        time = datetime.strptime(new_time, '%d.%m.%y %H:%M')
        time = mktime(time.timetuple())
        self.bot.db.update('forum', 'time', 'userid', time, 1)
        await ctx.send('Новое время установлено, нья!')

    @set_countdown.error
    async def set_countdown_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(f'{ctx.author.mention}, тебе низя использовать эту команду.')
        await ctx.send('Не получилось установить новое время')

    async def cog_command_error(self, ctx, error):
        print(ctx.command.name)
        if isinstance(error, commands.CheckFailure):
            channel = self.config['channel'].getint('transformator')
            await ctx.send(f'{ctx.author.mention}, тебе низя использовать эту команду туть. Сюда <#{channel}>')



    @commands.group(
        name = 'роль',
        brief='Настройка роли.',
        description='Обязательно указывайте название роли в "" (двойных кавычках <:ad:812513742000619520>)',
        help = 'create_role'
    )
    @commands.check(is_create_role_channel)
    async def role_settings(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('роль')


    @role_settings.command(
        name = 'добавить',
        aliases = ['создать'],
        usage = '<название роли> <цвет в 16ти>',
        description = 'Добавление новой роли',
        help = 'create_role'
    )
    async def create_new_role(self, ctx, name, color: ColorConverter):
        role = await ctx.guild.create_role(name = name, colour = color, hoist = True, mentionable = True)
        await ctx.author.add_roles(role)
        await ctx.send(f'{ctx.author.mention} Создала новую роль')

    @role_settings.command(
        name = 'удалить',
        usage = '<пинг роли>',
        description = 'Удаление ВАШЕЙ роли',
        help = 'create_role'
    )
    async def remove_role(self, ctx, role: RoleConverter = None):
        if not role:
            return await ctx.send_help('роль изменить название')
        if str(role.id) in self.config['roles'].values():
            return await ctx.send(f'{ctx.author.mention}, ДУРАААК ЭТО ОБЩАЯ РОЛЬ!')
        await role.delete()
        await ctx.send(f'{ctx.author.mention}, Удалила роль')

    @role_settings.group(
        name = 'изменить',
        description = 'Изменение ВАШЕЙ роли',
        help = 'create_role'
    )
    async def change_role(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f'{ctx.author.mention}, ты не указал что мне надо сделать, Баааака!')

    @change_role.command(
        name = 'название',
        usage = '<пинг роли> <новое название>',
        description = 'Изменение названия роли',
        help = 'create_role'
    )
    async def change_role_name(self, ctx, role: RoleConverter = None, name = None):
        if not role or not name:
            return await ctx.send_help('роль изменить название')
        if str(role.id) in self.config['roles'].values():
            return await ctx.send(f'{ctx.author.mention}, ДУРАААК ЭТО ОБЩАЯ РОЛЬ!')
        await role.edit(name = name)
        await ctx.send(f'{ctx.author.mention}, Изменила название')

    @change_role.command(
        name = 'цвет',
        usage = '<пниг роли> <новый цвет в 16ти>',
        description = 'Изменение цвета роли',
        help = 'create_role'
    )
    async def change_role_color(self, ctx, role: RoleConverter = None, color: ColorConverter = None):
        if not role or not color:
            return await ctx.send_help('роль изменить цвет')
        if str(role.id) in self.config['roles'].values():
            return await ctx.send(f'{ctx.author.mention}, ДУРАААК ЭТО ОБЩАЯ РОЛЬ!')
        await role.edit(colour = color)
        await ctx.send(f'{ctx.author.mention}, Изменила цвет')


    @role_settings.error
    async def role_settings_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            channel = self.config['channel'].getint('create_role')
            await ctx.send(f'{ctx.author.mention}, тебе низя использовать эту команду туть. Сюда <#{channel}>')

        if isinstance(error, commands.BadArgument):
            await ctx.send(f'{ctx.author.mention}, ты ввёл неправильные аргументы, бааака!')

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.mention}, ты ничего не ввёл, бааака!')

    @commands.command(
        name = 'закрепить',
        description = 'Закрепить сообщение из ответа',
        aliases = ['pin', 'закреп'],
    )
    async def pin_message(self, ctx):
        if ctx.message.reference:
            message = ctx.message.reference.resolved
            if message:
                await message.pin(reason=f'Message pinned by {ctx.author.name}')
                await ctx.reply('Закрепила сообщение')
        else:
            await ctx.reply('Ты не переслал какое сообщение закрепить надо, бака!')
    
    @commands.command(
        name = 'открепить',
        description = 'Открепить сообщение из ответа',
        aliases = ['unpin', 'откреп'],
    )
    async def unpin_message(self, ctx):
        if ctx.message.reference:
            message = ctx.message.reference.resolved
            if message:
                await message.unpin()
                await ctx.reply('Открепила сообщение')
        else:
            await ctx.reply('Ты не переслал какое сообщение открепить надо, бака!')





def setup(bot):
    bot.add_cog(Technical(bot))

'''
!роль добавить "название" "цвет"
!роль удалить "ID роли"
!роль изменить "ID роли" "что надо изменить название/цвет" "новое название/цвет"
'''
