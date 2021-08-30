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
4) на каждой странице по 4 арта со полной характеристикой и Id'шником

или же просмотр определённого арта по его ID в 16-ти ричном формате


Сборка билдов попозже, но что то похожее на просмотр только с добавлением в бланк перса


Планы на завтра:
    1. Сделать добавление арта у юзера +
    2. Начать делать показ
    3. Плеер?
'''

import discord
from discord.ext import commands
from bin.functions import *
from bin.checks import *
from bin.converters import *
from discord_components import Button, Select, ButtonStyle, SelectOption
from cogs.artifacts.extra import *
from cogs.artifacts.blanks import *

config = get_config()


class Artifacts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.get_cog('Database')






    @commands.Cog.listener()
    async def on_ready(self):
        self.db = self.bot.get_cog('Database')

    @commands.command(name='show', aliases=['показать'], usage='<member name>|<member ID>|<Nothing for yours>', description='Показ артов себя/пользователя')
    async def show_user_artifacts(self, ctx, *, member: UserConverter = None):

        member = member or ctx.author
        id = member.id

        async with ctx.typing():
            artifactsIDs = self.db.get_value(tableName = 'users_arts', argument = 'artifacts', selector = 'user_id', value = id)
            if not artifactsIDs:
                answer = f'<@{ctx.author.id}>, У тебя нет артефактов, бааака!'
                if len(splitter) > 1:
                    answer = f'<@{ctx.author.id}>, У этого пользователя нет артефактов, бааака!'
                await ctx.send(answer)
                return
            artifactsIDs = eval(artifactsIDs)
            username = await self.bot.fetch_user(id)
            author_name = 'Коллекция {}'.format(username.display_name)
            author_icon_URL = 'https://cdn.discordapp.com/attachments/813825744789569537/877565170258411550/user_account_person_avatar_icon_131248.png'


            fields = []

            for art in artifactsIDs:
                res = self.db.custom_command(f'SELECT * from artifacts where id = {int(art)};')[0]
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

    @show_user_artifacts.error
    async def not_found_user(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Не могу найти такого пользователя...')


    @commands.command(name='new', aliases=['арт'], usage='<part> <lvl>|<image>', description='Добавление нового артефакта', help = str(config['channel'].getint('artifact')))
    @is_channel(config['channel'].getint('artifact'))
    async def add_new_artifact(self, ctx, part: str = None, lvl: int = None):
        if part and lvl:
            response = await generate_blank(ctx, lvl = lvl, part = part)
            if response:
                new_artifact, embed, question = response
                res = put_artifact_in_database(self.db, ctx.author, new_artifact)
                if res:
                    footer = ['ID ' + '0' * (5 - len(str(res))) + str(res),
                                'https://cdn.discordapp.com/attachments/813825744789569537/877565862935150662/view_watch_eye_icon_131255.png']
                    author_name = 'Артефакт усешно создан и добавлен'
                    embed = get_embed(embed = embed, footer = footer, author_name = author_name)
                else:
                    author_name = 'Не удалось добавить артефакт...'
                    embed = get_embed(embed = embed, author_name = author_name)

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
            channel = config['channel'].getint('artifact')
            await ctx.send(f'Низя использовать эту команду туть. Тебе сюда <#{channel}>')
        else:
            await ctx.send(error)

def setup(bot):
    bot.add_cog(Artifacts(bot))
