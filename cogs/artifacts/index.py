'''
Артефакты

1) Добавление новых артов через скрин/вручную
2) Просмотр своих артов или чужих через select'ы
3) Сборка своего билда на персонажа (как вариант через селекты и кнопки)
4) ролить арты


Как выглядит бд:
Таблица всех артов (ID, типы всех статов, мейн стат, саб стат1, саб стат2, саб стат3, саб стат4)
Таблица юзеров и id их артов



Добавление новых артов:

1) вызов команды + скрин/пусто !добавить "часть" "уровень если не 20"
2) генерируется стартовый бланк арта либо на основе скрина, либо пустой полностью
3) через сообщения юзер обновляет/добавляет параметры арта
4) сохранение арта в бд
5) обновелнеи закрепа с ID-шниками юзеров
+

1. Пустой бланк с выбором сета
2. Если цветок или перо то мейн стат пишется сам, если нет, то выбор селектом мейн стата
3. луп на написание мейн стата
4. Выбор саб стата
5. луп заполнение саб стата
6. повторить ещё 3 раза


Просмотр артов:

1) выбор пользователя по ID
2) через селекты можно выбрать тип и сет
3) кнопки некст страницы
4) на каждой странице по 6 артов со полной характеристикой и Id'шником

или же просмотр определённого арта по его ID


Сборка билдов попозже, но что то похожее на просмотр только с добавлением в бланк перса


План в порядке важности:
    -1. Документация по артам для глупиков
    0. ПЕРЕНЕСТИ ВСЁ В КОНФИГ  +
    1. Автор артефакта при поиске +
    2. Разные топы  (общий топ, топ по части, топ по сету)
    3. Поменять веса статов
    4. Распознование картинки
'''

import discord
from discord.ext import commands
from bin.functions import *
from bin.checks import *
from bin.converters import *
from discord.ui import Button, Select
from discord import File, ButtonStyle, SelectOption
from cogs.artifacts.extra import *
from cogs.artifacts.blanks import *
from cogs.artifacts.pictures import create_pic_artifact


class Artifacts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config


    @commands.group(
        name='show',
        aliases=['показать'],
        description='Показ артов себя/пользователя'
    )
    async def show_user_artifact(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('show')


    @show_user_artifact.command(
        name='all',
        aliases=['все'],
        usage='<member name>|<member ID>|<Nothing for yours>',
        description='Показ артов себя/пользователя'
    )
    async def show_all_user_artifacts(self, ctx, *, member: UserConverter = None):
        member = member or ctx.author
        id = member.id
        async with ctx.typing():
            artifactsIDs = self.bot.db.get_value(tableName = 'users_arts', argument = 'artifacts', selector = 'user_id', value = id)
            if not artifactsIDs:
                answer = f'<@{ctx.author.id}>, У тебя нет артефактов, бааака!'
                if member != ctx.author:
                    answer = f'<@{ctx.author.id}>, У этого пользователя нет артефактов, бааака!'
                await ctx.send(answer)
                return
            artifactsIDs = eval(artifactsIDs)
            username = await self.bot.fetch_user(id)
            author_name = 'Коллекция {}'.format(username.display_name)
            author_icon_URL = 'https://cdn.discordapp.com/attachments/813825744789569537/877565170258411550/user_account_person_avatar_icon_131248.png'


            fields = []

            for art in artifactsIDs:
                res = self.bot.db.custom_command(f'SELECT * from artifacts where id = {int(art)};')[0]
                name = f'{res[2]} {res[3]} lvl\n{res[1]}\n{res[4]}'

                value = '**┏━━━━━┓**\n'
                for i in range(0, 8, 2):
                    space = ' ' * (14 - len(res[6 + i]) - len(res[7  + i]))
                    value += f'`{res[6 + i]}{space}{res[7 + i]}`\n'
                value += '**┗━━━━━┛**\n'

                zero = '0' * (5 - len(str(res[0])))
                value += f'   ID {zero}{res[0]}'
                fields.append({'name': name, 'value': value, 'inline': True})

            pages = [fields[i:i+6] for i in range(0, len(fields), 6)]
            page = 0

            components = get_query_btns(ctx, f'Page {page + 1}/{len(pages)}')
            embed = get_embed(author_name = author_name, author_icon_URL = author_icon_URL, fields = pages[page])
            question = await ctx.send(embed = embed, components = components)

        while True:
            def check(res):
                return res.channel == ctx.channel and res.author == ctx.author and res.message.id == question.id

            try:
                res = await self.bot.wait_for("button_click", check = check, timeout = 60.0)

            except:

                await question.edit(components = [])
                await question.delete(delay = 10)
                await ctx.message.delete(delay = 10)
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

                components = get_query_btns(ctx, f'Page {page + 1}/{len(pages)}')
                embed = get_embed(embed = embed, fields = pages[page])

                await res.respond(type=7, embed = embed, components = components)


    @show_user_artifact.command(
        name='id',
        usage='<artifact ID>',
        description='Показ определённого арта себя/пользователя'
    )
    async def show_user_artifact_by_ID(self, ctx, artifact_id: int):
        member = ctx.author
        #await ctx.send(f'ID {artifact_id}\nMemeber {member}')

        async with ctx.typing():
            artifact_data = self.bot.db.custom_command(f'SELECT * from artifacts where id = {artifact_id};')
            if not artifact_data:
                return await ctx.send(f'<@{ctx.author.id}>, Нет такого артефакта.')
            artifact_data = artifact_data[0]
            res = self.bot.db.get_all('artifacts')
            res = sorted(res, reverse=True, key=lambda item: item[15])


            artifact = Artifact(
                set = artifact_data[1],
                part = artifact_data[2],
                lvl = artifact_data[3],
                main = [artifact_data[4], artifact_data[5]],
                subs = [[artifact_data[i], artifact_data[i+1]] for i in range(6, 14, 2)],
                id = artifact_data[0]
            )
            artifact.part_url = artifact_data[14]
            artifact.gs = artifact_data[15]
            artifact.rate = f'{res.index(artifact_data) + 1}/{len(res)}'
            artifact_picture = create_pic_artifact(artifact, 'iconUSAGIlook')
            file = File(fp = artifact_picture.image_bytes, filename = "blank.png")
            users_data = self.bot.db.get_all('users_arts')
            author = None
            for user in users_data:
                if user[1]:
                    if artifact.id in eval(user[1]):
                        id = user[0]
                        author = await self.bot.fetch_user(user[0])
            embed = get_embed(
                        author_name=f'© {author.display_name}',
                        url_image = "attachment://blank.png",
                        author_icon_URL = author.avatar_url)

            question = await ctx.send(embed = embed, file = file)


    @show_user_artifact.error
    async def not_found_user(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Не могу найти такого пользователя...')


    @commands.command(
        name='new',
        aliases=['арт'],
        usage='<part> <lvl>|<image>',
        description='Добавление нового артефакта, пока работает только ввод ручками',
        help = 'artifact'
    )
    @commands.check(is_artifact_channel)
    async def add_new_artifact(self, ctx, part: str = None, lvl: int = None):
        if part and lvl:
            response = await generate_blank(ctx, lvl = lvl, part = part)
            if response:
                new_artifact, question = response
                print(str(new_artifact))
                res = put_artifact_in_database(self.bot.db, ctx.author, new_artifact)
                if res:
                    new_artifact.id = res
                    artifacts = self.bot.db.get_all('artifacts')
                    artifacts = sorted(artifacts, reverse=True, key=lambda item: item[15])
                    result = [x for x in artifacts if x[0] == res]
                    new_artifact.rate = f'{artifacts.index(result[0]) + 1}/{len(artifacts)}'
                    author_name = 'Артефакт успешно создан и добавлен'
                    blank = create_pic_artifact(new_artifact, 'iconUSAGIlook')
                    trash_channel = await ctx.bot.fetch_channel(self.config['channel']['trash_channel'])
                    blank_url = await get_blank_url(trash_channel, blank)
                    embed = get_embed(author_name = author_name, url_image = blank_url)
                else:
                    author_name = 'Не удалось добавить артефакт...'
                    embed = get_embed(author_name = author_name, url_image = 'https://cdn.discordapp.com/attachments/884802734627377232/884868744051052554/iconUSAGI_error.png')

                await question.edit(embed = embed, components = [])
                # await ctx.send('Successfully created artifact')
                # добавление нового артефакта в базу данных
            else:
                pass

        elif ctx.message.attachments:
            for attachment in ctx.message.attachments:
                await ctx.send(f'Ты прикрепил - {attachment.content_type}')
        else:
            raise commands.BadArgument


    @add_new_artifact.error
    async def new_artifacts_errors(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Неверные аргументы, Баака!')

        elif isinstance(error, commands.CheckFailure):
            channel = self.config['channel']['artifact']
            await ctx.send(f'Низя использовать эту команду туть. Тебе сюда <#{channel}>')
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help('new')
        else:
            await ctx.send(error)

    @commands.command(
        name='remove',
        aliases=['удалить'],
        usage='<artifact ID>',
        description='Удаление артефакта',
        help = 'artifact'
    )
    @commands.check(is_artifact_channel)
    async def remove_artifact(self, ctx, artifact_id: int):
        artifactsIDs = self.bot.db.get_value(tableName = 'users_arts', argument = 'artifacts', selector = 'user_id', value = ctx.author.id)
        if not artifactsIDs:
            return await ctx.send(f'<@{ctx.author.id}>, У тебя нет артефактов, бааака!')

        artifactsIDs = eval(artifactsIDs)
        if artifact_id not in artifactsIDs:
            return await ctx.send(f'<@{ctx.author.id}>, Это не твой артефакт, бааака!')

        response = self.bot.db.remove(tableName = 'artifacts', selector = 'id', value = artifact_id)
        if not response:
            return await ctx.send(f'<@{ctx.author.id}>, Не получилось удалить твой артефакт, пластити(')

        artifactsIDs.remove(artifact_id)
        response = self.bot.db.update(tableName = 'users_arts', argument = 'artifacts', selector = 'user_id', newValue = str(artifactsIDs), findValue = ctx.author.id)

        if not response:
            return await ctx.send(f'<@{ctx.author.id}>, Удалила артефакт, но у тебя его убрать не получилось, облатитесь к администрации.')
        return await ctx.send(f'<@{ctx.author.id}>, Успешно удалила, Нья!')


    @remove_artifact.error
    async def remove_artifact_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help('remove')


    @commands.group(
        name='top',
        aliases=['топ', 'рейтинг'],
        usage='',
        description='Рейтинг артефактов',
        help = 'artifact'
    )
    @commands.check(is_artifact_channel)
    async def top_artifact(self, ctx):
        res = self.bot.db.get_all('artifacts')
        artifactsIDs = sorted(res, reverse=True, key=lambda item: item[15])[:6]
        author_name = 'Топ всех артефактов'
        author_icon_URL = 'https://cdn.discordapp.com/attachments/813825744789569537/877565170258411550/user_account_person_avatar_icon_131248.png'


        fields = []

        for artifact in artifactsIDs:
            name = f'{artifact[2]} {artifact[3]} lvl\n{artifact[1]}\n{artifact[4]}'

            value = '**┏━━━━━┓**\n'
            for i in range(0, 8, 2):
                space = ' ' * (14 - len(artifact[6 + i]) - len(artifact[7  + i]))
                value += f'`{artifact[6 + i]}{space}{artifact[7 + i]}`\n'
            value += '**┗━━━━━┛**\n'

            zero = '0' * (5 - len(str(artifact[0])))
            value += f'   ID {zero}{artifact[0]}'
            fields.append({'name': name, 'value': value, 'inline': True})


        embed = get_embed(author_name = author_name, author_icon_URL = author_icon_URL, fields = fields)
        question = await ctx.send(embed = embed)




    @top_artifact.error
    async def top_artifact_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help('remove')


def setup(bot):
    bot.add_cog(Artifacts(bot))
