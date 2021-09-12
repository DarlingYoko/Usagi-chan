import discord, asyncio, requests
from cogs.artifacts.extra import *
from cogs.artifacts.errors import *
from cogs.artifacts.pictures import create_pic_artifact
from discord.ext import commands
from bin.functions import get_embed, print_error
from easy_pil import Editor, Canvas
from PIL import Image, ImageFont
from discord import File






async def generate_blank(ctx, set = None, lvl = None, part = None, main = None, sub1 = None, sub2 = None, sub3 = None, sub4 = None):
    part = part.lower()
    channel = ctx.channel

    translate_parts = {
        'цветок': ['flower', 'цветочек', 'цвяточек'],
        'перо': ['plume', 'feather', 'пёрышко', 'перышко'],
        'часы': ['sands', 'clock', 'часики'],
        'кубок': ['goblet', 'cup'],
        'шапка': ['circlet', 'crown', 'корона', 'шляпя', 'шляпа'],
    }



    translate_parts_list = translate_parts.keys()
    for items in translate_parts.values():
        translate_parts_list = [*translate_parts_list, *items]


    if lvl not in [16, 20] or part not in translate_parts_list:
        await ctx.send('<@{}> Неверный запрос, бака!'.format(ctx.author.id))
        return

    for name, translate in translate_parts.items():
        if part in translate:
            part = name

    parts = {'цветок': ['https://cdn.discordapp.com/attachments/813825744789569537/877563359808069692/flower.png', '𝓕𝓵𝓸𝔀𝓮𝓻', 'Цветок жизни'],
            'перо': ['https://cdn.discordapp.com/attachments/813825744789569537/877563356431659008/feather.png', '𝓟𝓵𝓾𝓶𝓮', 'Перо смерти'],
            'часы': ['https://cdn.discordapp.com/attachments/813825744789569537/877563350983245854/clock.png', '𝓢𝓪𝓷𝓭𝓼', 'Пески времени'],
            'кубок': ['https://cdn.discordapp.com/attachments/813825744789569537/877563363163533332/goblet.png', '𝓖𝓸𝓫𝓵𝓮𝓽', 'Кубок пространства'],
            'шапка': ['https://cdn.discordapp.com/attachments/813825744789569537/877563236147404840/circlet.png', '𝓒𝓲𝓻𝓬𝓵𝓮𝓽', 'Корона разума'],}


    sets = get_sets()

    all_stats, elements, main_stats = get_stats()

    subStat = ['ATK', 'ATK%', 'CRIT DMG', 'CRIT RATE', 'HP', 'HP%', 'DEF', 'DEF%', 'EM', 'ER',]

    main_stat = main_stats[part]

    author_name = 'Добавление нового артефакта'
    author_icon_URL = 'https://cdn.discordapp.com/attachments/813825744789569537/877650197122011166/icon-document_87920.png'

    trash_channel = await ctx.bot.fetch_channel(884802734627377232)
    initial = 'iconUSAGINoted'
    artifact = Artifact(set = None, part = parts[part][2], lvl = lvl, main = None, subs = [None, None, None, None], id = None)
    artifact.part_url = parts[part][0]

    blank = create_pic_artifact(artifact, initial)
    blank_url = await get_blank_url(trash_channel, blank)
    embed = get_embed(author_name = author_name, author_icon_URL = author_icon_URL, url_image = blank_url)

    emojiAccept = ctx.bot.get_emoji(874767321007276143)
    emojiExit = ctx.bot.get_emoji(874767320915005471)
    btnAccept = Button(style=ButtonStyle.green, emoji = emojiAccept, id = 'accept')
    btnExit = Button(style=ButtonStyle.red, emoji = emojiExit, id = 'exit')

    components = get_components("Выбор сета", sets.keys())
    components.append([btnAccept, btnExit])


    question = await ctx.send(embed = embed, components = components)


    def check(res):
        return res.channel == channel and res.author == ctx.author and res.message.id == question.id

    #while True:

    # Выбор сета

    tasks = get_tasks(ctx, check)

    while tasks:
        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            for x in done:
                res = x.result()
                if res.custom_id == 'select':
                    title = res.values[0]
                    artifact.set = title
                    artifact.part_url = sets[title][part]
                    blank = create_pic_artifact(artifact, initial)
                    blank_url = await get_blank_url(trash_channel, blank)
                    embed = get_embed(embed = embed, url_image = blank_url)
                    await res.respond(type=7, embed = embed)

                elif res.custom_id == 'accept':
                    if title != 'Сет не выбран':
                        tasks = []
                        break
                    else:
                        await res.respond(content = 'Сет не выбран!')
                elif res.custom_id == 'exit':
                    raise Exit

                tasks = get_tasks(ctx, check)
                #asyncio.exceptions.CancelledError
        except Exit:
            print('Exit')
            await quit(ctx, question)
            return
        except:
            await quit(ctx, question)
            return


    print('pass', res.custom_id)

    # Сет выбран луп закончен



    # Выбор мейн стата и добавление циферок

    if part == 'цветок': #на 4 10 17 + 204 вместо 203
        artifact.main = ['HP', all_stats['HP'][lvl]]
        subStat.remove('HP')

    elif part == 'перо':
        artifact.main = ['ATK', all_stats['ATK'][lvl]]
        subStat.remove('ATK')

    else:
        components = get_components("Выбор мейн стата", main_stat)
        components.append([btnAccept, btnExit])
        await res.respond(type=7, components = components)


        tasks = get_tasks(ctx, check)

        while tasks:
            try:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                for x in done:
                    res = x.result()
                    if res.custom_id == 'select':
                        artifact.main = [res.values[0], '—']
                        blank = create_pic_artifact(artifact, initial)
                        blank_url = await get_blank_url(trash_channel, blank)
                        embed = get_embed(embed = embed, url_image = blank_url)
                        await res.respond(type=7, embed = embed)

                    elif res.custom_id == 'accept':
                        if artifact.main:
                            tasks = []
                            break
                        else:
                            await res.respond(content = 'Мейн стат не выбран!')

                    elif res.custom_id == 'exit':
                        raise Exit

                    tasks = get_tasks(ctx, check)



            except Exit:
                await quit(ctx, question)
                return


        # Мейн стат выбран переходим к записи числа

        # Вычисление мейн стата
        if artifact.main[0] in subStat:
            subStat.remove(artifact.main[0])

        if list_check_entry(artifact.main[0], elements):
            artifact.main[1] = all_stats['elements'][lvl]
        else:
            artifact.main[1] = all_stats[artifact.main[0]][lvl]






    print('Main stat selected, pass')
    # Мейн стат выбран и записан

    percent = ['CRIT', '%', 'DMG', 'BONUS', 'ER']


    for i in range(4):
        components = get_components("Выбор {} саб стата".format(i + 1), subStat)
        components.append([btnAccept, btnExit])
        blank = create_pic_artifact(artifact, initial)
        blank_url = await get_blank_url(trash_channel, blank)
        embed = get_embed(embed = embed, url_image = blank_url)
        await res.respond(type=7, embed = embed, components = components)

        tasks = get_tasks(ctx, check)

        while tasks:
            try:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                for x in done:
                    res = x.result()
                    if res.custom_id == 'select':
                        artifact.subs[i] = [res.values[0], '—']
                        blank = create_pic_artifact(artifact, initial)
                        blank_url = await get_blank_url(trash_channel, blank)
                        embed = get_embed(embed = embed, url_image = blank_url)
                        await res.respond(type=7, embed = embed)


                    elif res.custom_id == 'accept':
                        if artifact.subs[i]:
                            tasks = []
                            break
                        else:
                            await res.respond(content = 'Саб стат {} не выбран!'.format(i))
                    elif res.custom_id == 'exit':
                        raise Exit

                    tasks = get_tasks(ctx, check)


            except Exit:
                await quit(ctx, question)
                return


        print('Sub stat {} selected'.format(i))

        subStat.remove(artifact.subs[i][0])
        components = get_buttons(ctx)
        await res.respond(type=7, components = components)

        number = ''
        state = artifact.subs[i][0]
        zero = True
        dot = True
        while True:

            try:
                res = await ctx.bot.wait_for("button_click", check = check, timeout = 60.0)

            except:
                await quit(ctx, question)
                return

            else:

                if res.component.id in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', ]:
                    number += res.component.id
                    zero = False
                    if list_check_entry(state, percent):
                        if '.' in number:
                            dot = True
                            zero = True
                        else:
                            dot = False
                    else:

                        dot = True



                    components = get_buttons(ctx, zero = zero, dot = dot)

                elif res.component.id == '.':
                    number += res.component.id
                    zero = True
                    dot = True
                    components = get_buttons(ctx, zero = zero, dot = dot)

                elif res.component.id == 'clear':
                    number = number[:-1]
                    if number:
                        components = get_buttons(ctx, zero = zero, dot = dot)
                    else:
                        zero = True
                        dot = True
                        components = get_buttons(ctx, zero = zero, dot = dot)

                elif res.component.id == 'clean entry':
                    number = ''
                    zero = True
                    dot = True
                    components = get_buttons(ctx, zero = zero, dot = dot)

                elif res.component.id == 'accept':
                    if number:
                        try:
                            testNumber = float(number)
                            if testNumber > all_stats[state]['max']:
                                await res.respond(content = 'Саб стат {} превышает возможный стат!'.format(i))
                                continue
                            if num_decimal_places(number) > 1 or ('.' in number and len(number.split('.')[1]) > 1):
                                await res.respond(content = 'В саб стате {} слишком много знаков после точки!'.format(i))
                                continue

                        except ValueError:
                            await res.respond(content = 'Саб стат {} заполнен неверно!'.format(i))
                            continue
                        else:
                            if list_check_entry(state, percent):
                                artifact.subs[i] = [state, float(number)]
                            break
                    else:
                        await res.respond(content = 'Саб стат {} не заполнен!'.format(i))
                        continue

                elif res.component.id == 'exit':
                    await quit(ctx, question)
                    return

                artifact.subs[i] = [state, int(number)]
                blank = create_pic_artifact(artifact, initial)
                blank_url = await get_blank_url(trash_channel, blank)
                embed = get_embed(embed = embed, url_image = blank_url)
                await res.respond(type=7, embed = embed, components = components)





    # Успешно созаднный арт надо добавить в бд
    artifact.rate()
    return artifact, question
