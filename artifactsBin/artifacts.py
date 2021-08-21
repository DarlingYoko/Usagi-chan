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

import os, sys
import asyncio
import discord
from discord_components import Button, Select, ButtonStyle, InteractionType, SelectOption
from src.functions import createEmbed, getCurrentTime, printError
from artifactsBin.extraFunc import *


class Artifacts:

    def __init__(self, client, config, db):
        self.client = client
        self.config = config
        self.db = db


    async def addNewArtifact(self, message):

        data = message.content.split('!арт')


        try:
            if data[1]:
                lvl = int(data[1].split()[1].rstrip())
                part = data[1].split()[0].rstrip()
                print(lvl, part)
                await self.generateBlank(message = message, lvl = lvl, part = part)

            else:
                pass
        except Exception as e:
            printError()


    async def showUserArtifacts(self, message):
        try:
            channel = message.channel
            splitter = message.content.split()
            id = message.author.id



            if len(splitter) > 1:
                try:
                    id = int(splitter[1])
                except ValueError:
                    member = discord.utils.find(lambda m: m.display_name.lower().startswith(splitter[1].lower()), message.guild.members)

                    if member:
                        id = member.id
                    else:
                        await channel.send(f'<@{message.author.id}>, Не удалось найти пользователя, бааака!')
                        return
            artifactsIDs = self.db.getValue(tableName = 'users_arts', argument = 'artifacts', selector = 'user_id', value = id)
            if not artifactsIDs:
                answer = f'<@{message.author.id}>, У тебя нет артефактов, бааака!'
                if len(splitter) > 1:
                    answer = f'<@{message.author.id}>, У этого пользователя нет артефактов, бааака!'
                await channel.send(answer)
                return
            artifactsIDs = eval(artifactsIDs)
            username = await self.client.fetch_user(id)
            authorName = 'Коллекция {}'.format(username.display_name)
            authorIconURL = 'https://cdn.discordapp.com/attachments/813825744789569537/877565170258411550/user_account_person_avatar_icon_131248.png'


            fields = []

            for art in artifactsIDs:
                res = self.db.command(f'SELECT * from artifacts where id = {int(art)};')[0]
                name = f'{res[2]} {res[3]} lvl\n{res[1]}\n{res[4]}'

                value = '**┏━━━━━┓**\n'
                for i in range(0, 8, 2):
                    space = ' ' * (14 - len(res[6 + i]) - len(res[7  + i]))
                    value += f'`{res[6 + i]}{space}{res[7 + i]}`\n'
                value += '**┗━━━━━┛**\n'

                zero = '0' * (5 - len(str(res[0])))
                value += f'   ID {zero}{res[0]}'
                fields.append({'name': name, 'value': value, 'inline': True})

            pages = [fields[i:i+6] for i in range(0, len(fields), 6)]
            page = 0

            components = getQueryBtns(self, f'Page {page + 1}/{len(pages)}')
            embed = createEmbed(authorName = authorName, authorIconURL = authorIconURL, fields = pages[page])
            question = await channel.send(embed = embed, components = components)

            while True:
                def check(res):
                    return res.channel == channel and res.author == message.author and res.message.id == question.id

                try:
                    res = await self.client.wait_for("button_click", check = check, timeout = 60.0)

                except:

                    await question.edit(components = [])
                    await question.delete(delay = 10)
                    await message.delete(delay = 10)
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

                    components = getQueryBtns(self, f'Page {page + 1}/{len(pages)}')
                    embed = createEmbed(authorName = authorName, authorIconURL = authorIconURL, fields = pages[page])

                    await res.respond(type=7, embed = embed, components = components)

        except:
            printError()

    def showArtifactByID(self):
        pass

    def updatePinMessage(self):
        pass

    async def generateBlank(self, message, set = None, lvl = None, part = None, main = None, sub1 = None, sub2 = None, sub3 = None, sub4 = None):
        part = part.lower()
        try:
            channel = await self.client.fetch_channel(self.config['data'].getint('mpChannel'))
            if part in ['корона', 'шляпя', 'шляпа']:
                part = 'шапка'

            parts = {'цветок': ['https://cdn.discordapp.com/attachments/813825744789569537/877563359808069692/flower.png', '𝓕𝓵𝓸𝔀𝓮𝓻'],
                    'перо': ['https://cdn.discordapp.com/attachments/813825744789569537/877563356431659008/feather.png', '𝓟𝓵𝓾𝓶𝓮'],
                    'часы': ['https://cdn.discordapp.com/attachments/813825744789569537/877563350983245854/clock.png', '𝓢𝓪𝓷𝓭𝓼'],
                    'кубок': ['https://cdn.discordapp.com/attachments/813825744789569537/877563363163533332/goblet.png', '𝓖𝓸𝓫𝓵𝓮𝓽'],
                    'шапка': ['https://cdn.discordapp.com/attachments/813825744789569537/877563236147404840/circlet.png', '𝓒𝓲𝓻𝓬𝓵𝓮𝓽'],}

            if lvl not in [16, 20] or part not in parts.keys():
                await channel.send('<@{}> Неверный запрос, бака!'.format(message.author.id))
                return

            sets = getSets()

            allStats, elements, mainStats = getStats()

            subStat = ['ATK', 'ATK%', 'CRIT DMG', 'CRIT RATE', 'HP', 'HP%', 'DEF', 'DEF%', 'EM', 'ER',]

            mainStat = mainStats[part]




            authorName = 'Добавление нового артефакта'
            authorIconURL = 'https://cdn.discordapp.com/attachments/813825744789569537/877650197122011166/icon-document_87920.png'
            thumbnail = parts[part][0]

            title = 'Сет не выбран'
            space = ' ' * (38 - len(parts[part][1]) - len(str(lvl)))
            description = '**{0}**{2}***{1}* 𝓵𝓿𝓵**'.format(parts[part][1], lvl, space)
            fields = self.generateText(main = main, subs = [sub1, sub2, sub3, sub4])


            embed = createEmbed(title = title, description = description, authorName = authorName, authorIconURL = authorIconURL, thumbnail = thumbnail, fields = fields)

            emojiAccept = self.client.get_emoji(874767321007276143)
            emojiExit = self.client.get_emoji(874767320915005471)
            btnAccept = Button(style=ButtonStyle.green, emoji = emojiAccept, id = 'accept')
            btnExit = Button(style=ButtonStyle.red, emoji = emojiExit, id = 'exit')

            components = self.getComponents("Выбор сета", sets.keys())
            components.append([btnAccept, btnExit])


            mes = await channel.send(embed = embed, components = components)


            def check(res):
                return res.channel == channel and res.author == message.author and res.message.id == mes.id

            #while True:

            # Выбор сета

            tasks = getTasks(self, check)

            while tasks:
                try:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                    for x in done:
                        res = x.result()
                        if res.custom_id == 'select':
                            title = res.component[0].label
                            thumbnail = sets[title][part]
                            fields = self.generateText(main = main, subs = [sub1, sub2, sub3, sub4])
                            embed = createEmbed(title = title, description = description, authorName = authorName, authorIconURL = authorIconURL, thumbnail = thumbnail, fields = fields)
                            await res.respond(type=7, embed = embed)

                        elif res.custom_id == 'accept':
                            if title != 'Сет не выбран':
                                tasks = []
                                break
                            else:
                                await res.respond(content = 'Сет не выбран!')
                        elif res.custom_id == 'exit':
                            raise Exception

                        tasks = getTasks(self, check)
#asyncio.exceptions.CancelledError

                except:
                    print('Exit')
                    components=[]
                    await mes.edit(components = components)
                    await mes.delete(delay = 10)
                    await message.delete(delay = 10)
                    return


            print('pass', res.custom_id)

            # Сет выбран луп закончен



            # Выбор мейн стата и добавление циферок

            if part == 'цветок': #на 4 10 17 + 204 вместо 203
                main = ['HP', allStats['HP'][lvl]]
                subStat.remove('HP')

            elif part == 'перо':
                main = ['ATK', allStats['ATK'][lvl]]
                subStat.remove('ATK')

            else:
                components = self.getComponents("Выбор мейн стата", mainStat)
                components.append([btnAccept, btnExit])
                fields = self.generateText(main = main, subs = [sub1, sub2, sub3, sub4])
                embed = createEmbed(title = title, description = description, authorName = authorName, authorIconURL = authorIconURL, thumbnail = thumbnail, fields = fields)
                await res.respond(type=7, embed = embed, components = components)


                tasks = getTasks(self, check)

                while tasks:
                    try:
                        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                        for x in done:
                            res = x.result()
                            if res.custom_id == 'select':
                                main = [res.component[0].label, '—']
                                fields = self.generateText(main = main, subs = [sub1, sub2, sub3, sub4])
                                embed = createEmbed(title = title, description = description, authorName = authorName, authorIconURL = authorIconURL, thumbnail = thumbnail, fields = fields)
                                await res.respond(type=7, embed = embed)

                            elif res.custom_id == 'accept':
                                if main:
                                    tasks = []
                                    break
                                else:
                                    await res.respond(content = 'Мейн стат не выбран!')

                            elif res.custom_id == 'exit':
                                raise Exception

                            tasks = getTasks(self, check)



                    except:
                        print('Exit')
                        components=[]
                        await mes.edit(components = components)
                        await mes.delete(delay = 10)
                        await message.delete(delay = 10)
                        return


                # Мейн стат выбран переходим к записи числа

                # Вычисление мейн стата
                if main[0] in subStat:
                    subStat.remove(main[0])

                if listCheckEntry(main[0], elements):
                    main[1] = allStats['elements'][lvl]
                else:
                    main[1] = allStats[main[0]][lvl]






            print('Main stat number selected, pass')
            # Мейн стат выбран и записан

            subs = {1: sub1, 2: sub2, 3: sub3, 4: sub4}
            percent = ['CRIT', '%', 'DMG', 'BONUS', 'ER']


            for i in range(1, 5):
                components = self.getComponents("Выбор {} саб стата".format(i), subStat)
                components.append([btnAccept, btnExit])
                fields = self.generateText(main = main, subs = [subs[1], subs[2], subs[3], subs[4]])
                embed = createEmbed(title = title, description = description, authorName = authorName, authorIconURL = authorIconURL, thumbnail = thumbnail, fields = fields)
                await res.respond(type=7, embed = embed, components = components)

                tasks = getTasks(self, check)

                while tasks:
                    try:
                        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                        for x in done:
                            res = x.result()
                            if res.custom_id == 'select':
                                subs[i] = [res.component[0].label, '—']
                                fields = self.generateText(main = main, subs = [subs[1], subs[2], subs[3], subs[4]])
                                embed = createEmbed(title = title, description = description, authorName = authorName, authorIconURL = authorIconURL, thumbnail = thumbnail, fields = fields)
                                await res.respond(type=7, embed = embed)


                            elif res.custom_id == 'accept':
                                if subs[i]:
                                    tasks = []
                                    break
                                else:
                                    await res.respond(content = 'Саб стат {} не выбран!'.format(i))
                            elif res.custom_id == 'exit':
                                raise Exception

                            tasks = getTasks(self, check)


                    except:
                        print('Exit')
                        components=[]
                        await mes.edit(components = components)
                        await mes.delete(delay = 10)
                        await message.delete(delay = 10)
                        return


                print('Sub stat {} selected'.format(i))

                subStat.remove(subs[i][0])
                components = self.getButtons()
                fields = self.generateText(main = main, subs = [subs[1], subs[2], subs[3], subs[4]])
                embed = createEmbed(title = title, description = description, authorName = authorName, authorIconURL = authorIconURL, thumbnail = thumbnail, fields = fields)
                await res.respond(type=7, embed = embed, components = components)

                number = ''
                state = subs[i][0]
                zero = True
                dot = True
                while True:

                    try:
                        res = await self.client.wait_for("button_click", check = check, timeout = 60.0)

                    except:
                        components=[]
                        await mes.edit(components = components)
                        await mes.delete(delay = 10)
                        await message.delete(delay = 10)
                        return

                    else:

                        if res.component.id in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', ]:
                            number += res.component.id
                            zero = False
                            if listCheckEntry(state, percent):
                                if '.' in number:
                                    dot = True
                                    zero = True
                                else:
                                    dot = False
                            else:

                                dot = True



                            components = self.getButtons(zero = zero, dot = dot)

                        elif res.component.id == '.':
                            number += res.component.id
                            zero = True
                            dot = True
                            components = self.getButtons(zero = zero, dot = dot)

                        elif res.component.id == 'clear':
                            number = number[:-1]
                            if number:
                                components = self.getButtons(zero = zero, dot = dot)
                            else:
                                zero = True
                                dot = True
                                components = self.getButtons(zero = zero, dot = dot)

                        elif res.component.id == 'clean entry':
                            number = ''
                            zero = True
                            dot = True
                            components = self.getButtons(zero = zero, dot = dot)

                        elif res.component.id == 'accept':
                            if number:
                                try:
                                    testNumber = float(number)
                                    if testNumber > allStats[state]['max']:
                                        await res.respond(content = 'Саб стат {} превышает возможный стат!'.format(i))
                                        continue
                                    if numDecimalPlaces(number) > 1 or ('.' in number and len(number.split('.')[1]) > 1):
                                        await res.respond(content = 'В саб стате {} слишком много знаков после точки!'.format(i))
                                        continue

                                except ValueError:
                                    await res.respond(content = 'Саб стат {} заполнен неверно!'.format(i))
                                    continue
                                else:
                                    if listCheckEntry(state, percent):
                                        subs[i] = [state, float(number)]
                                    break
                            else:
                                await res.respond(content = 'Саб стат {} не заполнен!'.format(i))
                                continue

                        elif res.component.id == 'exit':
                            components=[]
                            await mes.edit(components = components)
                            await mes.delete(delay = 10)
                            await message.delete(delay = 10)
                            return

                        subs[i] = [state, number]
                        fields = self.generateText(main = main, subs = [subs[1], subs[2], subs[3], subs[4]])
                        embed = createEmbed(title = title, description = description, authorName = authorName, authorIconURL = authorIconURL, thumbnail = thumbnail, fields = fields)
                        await res.respond(type=7, embed = embed, components = components)





            # Успешно созаднный арт надо добавить в бд
            request = f"INSERT INTO artifacts VALUES(DEFAULT, \'{title}\', \'{part}\', {lvl}, \'{main[0]}\', \'{main[1]}\'"

            for sub in [subs[1], subs[2], subs[3], subs[4]]:
                request += f", \'{sub[0]}\', \'{sub[1]}\'"

            request += ") RETURNING id;"
            respondRequest = self.db.command(request)
            footer = None
            authorName = 'Не получилось добавить артефакт('
            if respondRequest != 0:
                artifactsIDs = self.db.getValue(tableName = 'users_arts', argument = 'artifacts', selector = 'user_id', value = message.author.id)
                if artifactsIDs:
                    artifactsIDs = eval(artifactsIDs)
                    artifactsIDs.append(respondRequest[0][0])
                    respond = self.db.update(tableName = 'users_arts', argument = 'artifacts', selector = 'user_id', newValue = str(artifactsIDs), findValue = message.author.id)

                else:
                    artifactsIDs = [respondRequest[0][0]]
                    respond = self.db.insert('users_arts', message.author.id, str(artifactsIDs))

                if respond:
                    footer = ['ID ' + '0' * (5 - len(str(respondRequest[0][0]))) + str(respondRequest[0][0]),
                                'https://cdn.discordapp.com/attachments/813825744789569537/877565862935150662/view_watch_eye_icon_131255.png']
                    authorName = 'Артефакт усешно создан и добавлен'



            components=[]

            fields = self.generateText(main = main, subs = [subs[1], subs[2], subs[3], subs[4]])
            embed = createEmbed(title = title, description = description, authorName = authorName, authorIconURL = authorIconURL, thumbnail = thumbnail, fields = fields, footer = footer)
            await mes.edit(embed = embed, components = components)
            #await channel.send('Artifact successfully added~!')



        except Exception as e:
            printError()
            await mes.delete(delay = 10)
            await message.delete(delay = 10)



    def generateText(self, main = None, subs = [None, None, None, None]):

        result = []
        percent = ['CRIT', '%', 'DMG', 'BONUS', 'ER']

        if main:
            state = main.copy()
            state[1] = str(state[1])
            if listCheckEntry(state[0], percent):
                state[1] += '%'
            res = '`{0}{1}{2}{3}{4}`'.format(state[0], ' '*(13-len(state[0])), '—', ' '*(13-len(state[1])), state[1])
        else:
            res = '`—{}—`'.format(' '*25)
        result.append({'name': res, 'value': '_ _', 'inline': False})
        result.append({'name': '┏━━━━━━━━━━━┓', 'value': '_ _', 'inline': False})

        for sub in subs:

            if sub:
                state = sub.copy()
                state[1] = str(state[1])
                if listCheckEntry(state[0], percent):
                    state[1] += '%'
                res = '`{0}{1}{2}{3}{4}`'.format(state[0], ' '*(13-len(state[0])), '—', ' '*(13-len(state[1])), state[1])
            else:
                res = '`—{}—`'.format(' '*25)
            result.append({'name': res, 'value': '_ _', 'inline': False})


        result.append({'name': '┗━━━━━━━━━━━┛', 'value': '_ _', 'inline': False})
        return result

    def getComponents(self, label, list):
        components=[
                    Select(
                        placeholder=label,
                        options=[SelectOption(label=item, value=item) for item in list],
                        custom_id="select",
                        ),
                    ]
        return components

    def getButtons(self, zero = True, dot = True):
        btn1 = Button(style=ButtonStyle.gray, label = '1', id = '1')
        btn2 = Button(style=ButtonStyle.gray, label = '2', id = '2')
        btn3 = Button(style=ButtonStyle.gray, label = '3', id = '3')
        btn4 = Button(style=ButtonStyle.gray, label = '4', id = '4')
        btn5 = Button(style=ButtonStyle.gray, label = '5', id = '5')
        btn6 = Button(style=ButtonStyle.gray, label = '6', id = '6')
        btn7 = Button(style=ButtonStyle.gray, label = '7', id = '7')
        btn8 = Button(style=ButtonStyle.gray, label = '8', id = '8')
        btn9 = Button(style=ButtonStyle.gray, label = '9', id = '9')
        btn0 = Button(style=ButtonStyle.gray, label = '0', id = '0', disabled = zero)
        btnDot = Button(style=ButtonStyle.gray, label = '.', id = '.', disabled = dot)

        btnInvisible = Button(style=ButtonStyle.gray, label = '-', disabled = True)


        emojiClear = self.client.get_emoji(873921151372513312)
        emojiAccept = self.client.get_emoji(874767321007276143)
        emojiCleanEntry = '🔙'
        emojiExit = self.client.get_emoji(874767320915005471)


        btnClear = Button(style=ButtonStyle.gray, emoji = emojiClear, id = 'clear')
        btnAccept = Button(style=ButtonStyle.green, emoji = emojiAccept, id = 'accept')
        btnCleanEntry = Button(style=ButtonStyle.red, emoji = emojiCleanEntry, id = 'clean entry')
        btnExit = Button(style=ButtonStyle.red, emoji = emojiExit, id = 'exit')

        components=[[btn1, btn2, btn3, btnClear], [btn4, btn5, btn6, btnCleanEntry], [btn7, btn8, btn9, btnAccept], [btnInvisible, btn0, btnDot, btnExit], ]

        return components
