import discord, asyncio
from cogs.artifacts.extra import *
from cogs.artifacts.errors import *
from discord.ext import commands
from bin.functions import get_embed, print_error



class Artifact:
    def __init__(self, set, part, lvl, main, subs):
        self.set = set
        self.part = part
        self.lvl = lvl
        self.main = main
        self.subs = subs


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

        parts = {'цветок': ['https://cdn.discordapp.com/attachments/813825744789569537/877563359808069692/flower.png', '𝓕𝓵𝓸𝔀𝓮𝓻'],
                'перо': ['https://cdn.discordapp.com/attachments/813825744789569537/877563356431659008/feather.png', '𝓟𝓵𝓾𝓶𝓮'],
                'часы': ['https://cdn.discordapp.com/attachments/813825744789569537/877563350983245854/clock.png', '𝓢𝓪𝓷𝓭𝓼'],
                'кубок': ['https://cdn.discordapp.com/attachments/813825744789569537/877563363163533332/goblet.png', '𝓖𝓸𝓫𝓵𝓮𝓽'],
                'шапка': ['https://cdn.discordapp.com/attachments/813825744789569537/877563236147404840/circlet.png', '𝓒𝓲𝓻𝓬𝓵𝓮𝓽'],}



        sets = get_sets()

        all_stats, elements, main_stats = get_stats()

        subStat = ['ATK', 'ATK%', 'CRIT DMG', 'CRIT RATE', 'HP', 'HP%', 'DEF', 'DEF%', 'EM', 'ER',]

        main_stat = main_stats[part]

        author_name = 'Добавление нового артефакта'
        author_icon_URL = 'https://cdn.discordapp.com/attachments/813825744789569537/877650197122011166/icon-document_87920.png'
        thumbnail = parts[part][0]

        title = 'Сет не выбран'
        space = ' ' * (38 - len(parts[part][1]) - len(str(lvl)))
        description = '**{0}**{2}***{1}* 𝓵𝓿𝓵**'.format(parts[part][1], lvl, space)
        fields = generate_text(main = main, subs = [sub1, sub2, sub3, sub4])


        embed = get_embed(title = title, description = description, author_name = author_name, author_icon_URL = author_icon_URL, thumbnail = thumbnail, fields = fields)

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
                        thumbnail = sets[title][part]
                        fields = generate_text(main = main, subs = [sub1, sub2, sub3, sub4])
                        embed = get_embed(embed = embed, title = title, thumbnail = thumbnail, fields = fields)
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
                print_error()
                return


        print('pass', res.custom_id)

        # Сет выбран луп закончен



        # Выбор мейн стата и добавление циферок

        if part == 'цветок': #на 4 10 17 + 204 вместо 203
            main = ['HP', all_stats['HP'][lvl]]
            subStat.remove('HP')

        elif part == 'перо':
            main = ['ATK', all_stats['ATK'][lvl]]
            subStat.remove('ATK')

        else:
            components = get_components("Выбор мейн стата", main_stat)
            components.append([btnAccept, btnExit])
            fields = generate_text(main = main, subs = [sub1, sub2, sub3, sub4])
            embed = get_embed(embed = embed, fields = fields)
            await res.respond(type=7, embed = embed, components = components)


            tasks = get_tasks(ctx, check)

            while tasks:
                try:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                    for x in done:
                        res = x.result()
                        if res.custom_id == 'select':
                            main = [res.values[0], '—']
                            fields = generate_text(main = main, subs = [sub1, sub2, sub3, sub4])
                            embed = get_embed(embed = embed, fields = fields)
                            await res.respond(type=7, embed = embed)

                        elif res.custom_id == 'accept':
                            if main:
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
            if main[0] in subStat:
                subStat.remove(main[0])

            if list_check_entry(main[0], elements):
                main[1] = all_stats['elements'][lvl]
            else:
                main[1] = all_stats[main[0]][lvl]






        print('Main stat number selected, pass')
        # Мейн стат выбран и записан

        subs = {1: sub1, 2: sub2, 3: sub3, 4: sub4}
        percent = ['CRIT', '%', 'DMG', 'BONUS', 'ER']


        for i in range(1, 5):
            components = get_components("Выбор {} саб стата".format(i), subStat)
            components.append([btnAccept, btnExit])
            fields = generate_text(main = main, subs = [subs[1], subs[2], subs[3], subs[4]])
            embed = get_embed(embed = embed, fields = fields)
            await res.respond(type=7, embed = embed, components = components)

            tasks = get_tasks(ctx, check)

            while tasks:
                try:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                    for x in done:
                        res = x.result()
                        if res.custom_id == 'select':
                            subs[i] = [res.values[0], '—']
                            fields = generate_text(main = main, subs = [subs[1], subs[2], subs[3], subs[4]])
                            embed = get_embed(embed = embed, fields = fields)
                            await res.respond(type=7, embed = embed)


                        elif res.custom_id == 'accept':
                            if subs[i]:
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

            subStat.remove(subs[i][0])
            components = get_buttons(ctx)
            fields = generate_text(main = main, subs = [subs[1], subs[2], subs[3], subs[4]])
            embed = get_embed(embed = embed, fields = fields)
            await res.respond(type=7, embed = embed, components = components)

            number = ''
            state = subs[i][0]
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
                                    subs[i] = [state, float(number)]
                                break
                        else:
                            await res.respond(content = 'Саб стат {} не заполнен!'.format(i))
                            continue

                    elif res.component.id == 'exit':
                        await quit(ctx, question)
                        return

                    subs[i] = [state, number]
                    fields = generate_text(main = main, subs = [subs[1], subs[2], subs[3], subs[4]])
                    embed = get_embed(embed = embed, fields = fields)
                    await res.respond(type=7, embed = embed, components = components)





        # Успешно созаднный арт надо добавить в бд

        fields = generate_text(main = main, subs = [subs[1], subs[2], subs[3], subs[4]])
        embed = get_embed(embed = embed, fields = fields)

        return Artifact(title, part, lvl, main, [subs[1], subs[2], subs[3], subs[4]]), embed, question





        components=[]


        await question.edit(embed = embed, components = components)
        #await channel.send('Artifact successfully added~!')
        return
