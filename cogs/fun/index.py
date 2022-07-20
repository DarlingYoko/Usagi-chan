from calendar import c
import discord
import random, requests, re
from discord.ext import commands
from bin.converters import *
from bin.functions import get_member_by_all
from bs4 import BeautifulSoup
from datetime import datetime

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config


    @commands.command(
        description = 'Проверка пинга',
        aliases = ['пинг'],
        brief='Проверка пинга'
    )
    async def ping(self, ctx):
        await ctx.send(f'Pong! {round(ctx.bot.latency * 1000)} ms')

    @commands.command(
        name = 'check',
        aliases = ['чек'],
        description = 'Поиск юзера',
        brief='Узнать когда юзер зашёл',
        usage = '<имя пользователя>|<ID>'
    )
    async def joined(self, ctx, *, member: str = None):
        member = await get_member_by_all(self, member) or ctx.author
        time = member.joined_at.strftime("%m/%d/%Y, %H:%M")
        req = await self.bot.http.request(discord.http.Route("GET", "/users/{uid}", uid=member.id))
        banner_id = req["banner"]
        banner_url = ''
        if banner_id:
            banner_url = f"https://cdn.discordapp.com/banners/{member.id}/{banner_id}?size=1024"
        await ctx.send(f'{member} joined on {time}\n{member.avatar}\n{banner_url}')

    @joined.error
    async def joined_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('I could not find that member...')

    @commands.command(
        aliases=['число'],
        usage='<from>-<to>',
        description='Роллим гачу <:ad:812513742000619520>',
        brief='Рандом число <от>-<до>'
    )
    async def roll(self, ctx, *, args = None):
        if args is None:
            #raise commands.BadArgument
            return await ctx.send_help('roll')

        args = args.split('-')
        if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
            raise commands.BadArgument

        try:
            number = random.randint(int(args[0]), int(args[1]))
        except ValueError:
            raise commands.BadArgument
        await ctx.send(f'Yours roll is {number}')

    @roll.error
    async def joined_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('<:MonkaStop:837405113638977576>')



    @commands.command(name = 'вебивент', aliases = ['веб', 'ивент'])
    async def web_event_link(self, ctx):
        links = self.config['web_event']['links'].split(',')
        links = list(map(lambda x: f'<{x}>', links))
        return await ctx.send('Текущие ссылки на веб ивент:\n' + '\n'.join(links))

    @commands.is_owner()
    @commands.command()
    async def set_web_event_link(self, ctx, links: str):
        self.config['web_event']['links'] = links
        with open('./test_config/variables.ini', "w") as config_file:
            self.config.write(config_file)
        return await ctx.send('Записала новые ссылки')

    @commands.command(name = 'примогемы')
    async def primogems_link(self, ctx):
        return await ctx.send('<https://docs.google.com/spreadsheets/d/1DPJOtHTLB_y-MTcUheSBrMPFvV_EtBlcYA6Xy1F0R_c/edit?pli=1#gid=284498967>')

    @commands.command(name = 'форум', aliases = ['forum'])
    async def forum_link(self, ctx):
        return await ctx.send('Ссылка на форум - <https://www.hoyolab.com>\nСсылка на логин бонус - <https://webstatic-sea.mihoyo.com/ys/event/signin-sea/index.html?act_id=e202102251931481&lang=ru-ru>')

    @commands.command(name = 'карта', aliases = ['map'])
    async def map_link(self, ctx):
        return await ctx.send('Интерактивная карта по Геншину: <https://webstatic-sea.mihoyo.com/app/ys-map-sea/?lang=ru-ru>')

    @commands.command(name = 'хх', aliases = ['hh'])
    async def hh_link(self, ctx):
        return await ctx.send('<https://genshin.honeyhunterworld.com>')

    @commands.command(name = 'паймон')
    async def paimon_link(self, ctx):
        return await ctx.send('https://paimon.moe/')

    @commands.command(name = 'яишенка', aliases = ['глазунья'])
    async def jaishenka(self, ctx):
        answer = ('<a:read:859186021488525323> Ставишь сковороду на небольшую температуру, наливаешь немного масла, растираешь силиконовой кисточкой или салфеткой равномерно, чтобы не хлюпало, разбиваешь яйцо и ждёшь\n\n' +
                    '<a:read:859186021488525323> Видишь, что нижний слой белка начинает белеть, а сверху вокруг желтка еще сопелька прозрачная, так вот, бери вилочку и под сопелькой в радиусе разлива яйца разрывай белок, чтобы слой вокруг желтка тип провалился к сковородке и стал одним целым со всем белком, посыпаешь приправами на вкус, ждешь, огонь сильно не добавляешь и готово\n\n' +
                    '<a:peepoFAT:859363980228427776> Если любишь, чтобы желток внутри приготовился и был не жидкий, то накрываешь крышкой')
        return await ctx.send(answer)


    @commands.command(aliases = ['арольф', 'арофл'])
    async def arolf(self, ctx):
        arolf_file = discord.File('files/photo/aRolf.png')
        return await ctx.send(file = arolf_file)

    @commands.command(aliases = ['токсины'])
    async def toxic(self, ctx):
        return await ctx.send(f'Уровень токсинов в чате {random.randint(1, 100)}% <:peepoSitStarege:933802101824430201>')

    @commands.command(aliases = ['ссылочки', 'круточки'])
    async def link(self, ctx):
        return await ctx.send('Запись стримов и круточек - <https://www.twitch.tv/yoko_o0>\nВесь материальчик по кадровому <https://www.youtube.com/channel/UCgis0wZn_m5mFNQHzvqyf8w>')

    @commands.command(aliases = ['база'])
    async def base_message(self, ctx, message_link=None):
        channel = await ctx.bot.fetch_channel(942169382124134410)
        if ctx.message.attachments:
            files = None
            file_ = None
            if len(ctx.message.attachments) > 1:
                files = []
                for file in ctx.message.attachments:
                    file = await file.to_file()
                    files.append(file)
            else:
                file_ = await ctx.message.attachments[0].to_file()
            await channel.send(content=f'База от {ctx.message.author.mention}',
                               files=files,
                               file=file_
                               )
            await ctx.send('Добавила базу <:BASEDHM:897821614312394793>')
            return None
        try:
            message_id = message_link.split('/')[6]
            channel_id = message_link.split('/')[5]
            mes_channel = await ctx.bot.fetch_channel(channel_id)
            message = await mes_channel.fetch_message(message_id)
        except:
            return await ctx.send('Не нашла базу(')
        files = None
        file_ = None
        if message.attachments:
            if len(message.attachments) > 1:
                files = []
                for file in message.attachments:
                    file = await file.to_file()
                    files.append(file)
            else:
                file_ = await message.attachments[0].to_file()
        await channel.send(content=f'База от {message.author.mention}\n{message.content}',
                           files=files,
                           file=file_,
                           embeds=message.embeds,
                           )
        await ctx.send('Добавила базу <:BASEDHM:897821614312394793>')

    @commands.command(name='курс')
    @commands.cooldown(per=60*1, rate=1)
    async def get_currency(self, ctx):
        url = 'https://ru.tradingview.com/markets/currencies/rates-europe/'

        r = requests.get(url)
        # print(r)
        soup = BeautifulSoup(r.text, 'html.parser')
        # print(soup)
        table = soup.find_all('tr')[1:]
        # print(len(table))
        currencys = {}
        for currency in table:
            name = currency.find('a').text
            # print(currency)
            if name in ['USDRUB', 'USDUAH', 'USDBYN']:
                value = currency.find_all('td')[1].text
                change = currency.find_all('td')[3].text
                # print(name, value, change)
                currencys[name] = {'value': value, 'change': change}
        url = 'https://ru.tradingview.com/markets/currencies/rates-asia/'

        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find_all('tr')[1:]
        # print(len(table))
        for currency in table:
            name = currency.find('a').text
            # print()
            if name == 'USDKZT':
                value = currency.find_all('td')[1].text
                change = currency.find_all('td')[3].text
                currencys[name] = {'value': value, 'change': change}
                break

        
       

            # f"{numObj:.{digits}f}"
        # print(currencys)
        beer = self.bot.get_cog('Beer')
        # 2. Бел рубль {currencys["USDBYN"]["value"]} ({currencys["USDBYN"]["change"]})
        text = f'''```autohotkey
Сводка курса на данный момент:\n'''
# 5. Усаги коины к дабаби {beer.currenсy} к 1
        counter = 1
        for key in currencys:
            text += f'{counter}. {key} {currencys[key]["value"]} ({currencys[key]["change"]})\n'
            counter += 1
        text += '```'
        await ctx.send(content=text)

    #@commands.command()
    #async def test(self, ctx, user: discord.Member, role: discord.Role):
    #    return await user.add_roles(role)
    @commands.command(name='теги')
    # @commands.cooldown(per=60*1, rate=1)
    async def get_tags(self, ctx, id):
        url = f'https://nhentai.net/g/{id}/'

        r = requests.get(url)
        if r.status_code != 200:
            return await ctx.send('Такого нет палучается')
        soup = BeautifulSoup(r.text, 'html.parser')

        tags_div = soup.find('section', {'id': 'tags'}).find_all('div')

        for tag_div in tags_div:
            if 'Tags:' in tag_div.text:
                field = tag_div.find('span', {'class': 'tags'})
                tags = field.find_all('a')
                tags_info = {}
                for tag in tags:
                    
                    name = tag.find('span', {'class': 'name'}).text
                    count = tag.find('span', {'class': 'count'}).text
                    # print(name, count)
                    tags_info[name] = count
                break


        print(tags_info)

        text = '```autohotkey\n'
        counter = 1
        for key, value in tags_info.items():
            text += f'{counter}. {key}:{value}\n'
            counter += 1
        text += '```\n'
        text += f'Ссылка - <{url}>'

        await ctx.send(content=text)

    @commands.command(name='iq', help='toxic')
    @commands.cooldown(per=60*1, rate=1, type=commands.BucketType.user)
    async def get_iq(self, ctx):
        iq = random.randint(1, 201)
        text = f'{ctx.message.author.mention} Твой iq = {iq}\n'
        if iq <= 110 and iq >= 90:
            text += 'Не ну ты чисто очередняря'
        if iq < 200 and iq >= 170:
            text += 'Пчел пытается быть умным aRolf'
        elif iq == 1:
            text += 'ПЧЕЛ ТЫЫЫ НУЛИНА, соболезную чатерсам'
        elif iq == 200:
            text += 'А ты хорош, я бы даже сказала МЕГАХАРОШ'
        elif iq == 69:
            text += '+ секс'
        elif iq < 50:
            text += 'Мдааааа, какой же ты тупой'
        await ctx.send(content=text)

    @get_iq.error
    async def wordle_top_errors(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = float(error.retry_after)
            await ctx.send(f'{ctx.author.mention} Пока рано для определения твоего IQ, подожди {retry_after:.2f} секунд')

    # @commands.command(name='пиво', aliases=['пыво', 'beer', 'пивко'])
    # @commands.cooldown(per=60*1, rate=1, type=commands.BucketType.user)
    # async def get_iq(self, ctx):
    #     pass
    
    @commands.is_owner()
    @commands.command()
    async def test(self, ctx):
        # c = {917896025849606145: (58, 36, 0, 3, 0, ''), 866083224354684928: (4956, 730, 0, 58, 0, ''), 864765911663116288: (5771, 1228, 18, 1053, 41, ''), 860284431029501952: (208, 15, 0, 1, 0, ''), 824521926416269312: (1068, 93, 4, 17, 1, ''), 793963638901833769: (13, 4, 0, 0, 0, ''), 793409024015073281: (44219, 20848, 653, 4373, 512, ''), 750563921584193577: (17547, 8260, 29, 3280, 18, ''), 734108286248288281: (11668, 5240, 194, 286, 83, ''), 721761390725038161: (25396, 5163, 72, 386, 49, ''), 689134347516903425: (19097, 5722, 188, 219, 0, ''), 686586463357370449: (87338, 18574, 456, 743, 2, ''), 681151018922410048: (29, 11, 0, 0, 0, ''), 674650795525799994: (47384, 18577, 409, 384, 19, ''), 606900908579880992: (1219, 819, 0, 93, 31, ''), 575338259031392276: (21365, 8193, 180, 3126, 149, ''), 559399135195693079: (77, 39, 0, 2, 0, ''), 532323484924116992: (39997, 11576, 29, 3319, 10, ''), 509446686171463690: (95, 2, 0, 2, 0, ''), 507901141116518415: (50640, 11219, 187, 1584, 75, ''), 498249577699344384: (27777, 17714, 1073, 567, 326, ''), 480462696802680842: (60274, 38222, 909, 4552, 180, ''), 452021696346456085: (25361, 15067, 1166, 2076, 12, ''), 432227036472541184: (460, 125, 6, 47, 12, ''), 417334123301175297: (255, 148, 19, 38, 0, ''), 409436915117326338: (52073, 38145, 850, 4083, 43, ''), 397085339292008449: (22327, 8300, 414, 4434, 684, ''), 385069724486074378: (4014, 720, 45, 332, 20, ''), 369138872048943115: (82137, 24489, 266, 1981, 544, ''), 357540566843523073: (83237, 9513, 409, 1340, 104, ''), 341610000264724511: (1525, 410, 12, 116, 6, ''), 341222213409701899: (25927, 1705, 1, 1151, 0, ''), 335954146765045761: (26480, 11285, 304, 3306, 111, ''), 332882488961662978: (39666, 15735, 342, 457, 2, ''), 329174370562080778: (6652, 3097, 21, 183, 29, ''), 325604243925106688: (658, 154, 6, 37, 4, ''), 324159705544916992: (16637, 9849, 41, 1537, 131, ''), 322388684034932736: (451, 72, 1, 2, 0, ''), 311415107928457226: (3230, 74, 24, 1, 0, ''), 307491897562234884: (13831, 4772, 486, 677, 209, ''), 304578501351047178: (58588, 21295, 407, 3608, 94, ''), 303623084429148161: (30121, 8150, 179, 2376, 66, ''), 300483698665586689: (7301, 4519, 87, 832, 18, ''), 300281175942103040: (14273, 3926, 115, 641, 44, ''), 298740173741621270: (42367, 17925, 1430, 3428, 219, ''), 294905624464982016: (47272, 4497, 8, 92, 0, ''), 290166276796448768: (29152, 9678, 233, 3345, 125, ''), 289479328830586880: (55, 2, 0, 0, 0, ''), 289361805279494145: (24493, 11646, 327, 1238, 123, ''), 282838803289341954: (19655, 8736, 4, 813, 58, ''), 276427191217160202: (68125, 34526, 253, 4594, 47, ''), 269453719303618560: (20228, 5308, 47, 478, 8, ''), 260076356597972993: (17700, 3144, 69, 64, 2, ''), 259754214341738497: (58578, 31479, 1967, 5213, 685, ''), 253520491422285834: (15, 0, 0, 0, 0, ''), 249874183943749632: (78931, 15011, 471, 2084, 120, ''), 249146637618905088: (32130, 9734, 24, 2180, 127, ''), 243658118372917248: (16851, 2325, 124, 1080, 109, ''), 241182014181474304: (7318, 2018, 17, 856, 87, ''), 234419004008038411: (1146, 516, 62, 44, 4, ''), 230863156174520320: (2365, 1602, 21, 290, 11, ''), 224812444462088194: (13301, 6253, 762, 1340, 226, ''), 212894057884549121: (2025, 1077, 30, 229, 1, ''), 203616268618563584: (17405, 14174, 87, 1252, 319, ''), 198013978079657984: (44755, 12545, 57, 4093, 1020, ''), 197830830213693441: (7463, 4319, 1, 399, 4, ''), 197127942784942080: (387, 196, 1, 32, 0, ''), 185353739278745600: (60525, 12839, 329, 594, 227, ''), 183310604692357120: (109, 69, 0, 4, 0, ''), 182131285051965440: (5627, 4423, 19, 354, 27, ''), 127990560538492928: (50739, 16295, 10, 2597, 2, ''), 752055514497548360: (11, 0, 0, 4, 3, ''), 257573093126569988: (90, 2, 0, 32, 11, ''), 252000672415744001: (36, 9, 0, 28, 3, ''), 619982406354731025: (166, 2, 0, 71, 4, ''), 548794687587352576: (3, 2, 0, 0, 1, ''), 276388874031464448: (13, 0, 1, 3, 7, ''), 268691598102102017: (28, 0, 0, 20, 1, '')}
        # sql = ''
        # for key, value in c.items():
        #     sql += f'insert into statistic values ({key}, {value[0]}, {value[1]}, {value[2]}, {value[3]}, {value[4]}, \'\');\n'
        # self.bot.db.custom_command(sql)
        print('start searching')
        guild = await self.bot.fetch_guild(858053936313008129)
        # members = await guild.fetch_members(limit=None).flatten()
        # users = {}
        # for member in members:
        #     datas = self.bot.db.custom_command(f'select * from statistic where user_id = {member.id};')
        #     if not datas:
        #         continue
        #     data = datas[-1]
        #     users[data[0]] = data[1:]
        # print(users)
            # for data in datas:
            #     if member.id in users.keys():
            #         pass
        users = {}
        text_channel = await guild.fetch_channel(863966092153192478)

        channels = await guild.fetch_channels()
        # threads = await guild.active_threads()
        

        threads_ids = [881983857019191296, 
            957040305222348860,
            889243020707369031,
            932628946443468841,
            870347994669662249,
            880810276981714954,
            895049999228993556,
            875431191245885460,
            931920673297801256,
            873264415368179773,
            941774848886190090
        ]
        threads = []
        for thread_id in threads_ids:
            threads.append(await guild.fetch_channel(thread_id))
        channels += threads

        for channel in channels:

            print(f'start with channel {channel.name}')
            history = []
            if not (channel.type == discord.ChannelType.text or \
                    channel.type == discord.ChannelType.private or \
                    channel.type == discord.ChannelType.group or \
                    channel.type == discord.ChannelType.public_thread or \
                    channel.type == discord.ChannelType.private_thread):
                continue
            first_message = await channel.history(limit=1, oldest_first=True).flatten()
            first_message = first_message[0]
            history.append(first_message)
            messages = await channel.history(limit=200, after=first_message).flatten()
            # print(len(messages), channel.name)
            while len(messages) == 200:
                history += messages
                messages = await channel.history(limit=200, after=messages[-1]).flatten()
            history += messages
            print(len(history))
            for message in history:
                if message.author.bot:
                    continue

                user_id = message.author.id
                if user_id not in users.keys():
                    users[user_id] = {}
                    # 'message': 0, 'image': 0, 'gifs': 0, 'emoji': 0, 'sticker': 0
                
                if message.channel.id not in users[user_id].keys():
                    users[user_id][message.channel.id] = {'message': 0, 'image': 0, 'gif': 0, 'emoji': 0, 'sticker': 0}

                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.content_type in ['image/png', 'image/jpeg', 'image/jpg']:
                            users[user_id][message.channel.id]['image'] += 1
                        if attachment.content_type in ['image/gif']:
                            users[user_id][message.channel.id]['gif'] += 1
                if '.gif' in message.content:
                    users[user_id][message.channel.id]['gif'] += 1
                if re.search('<*:*:*>', message.content):
                    users[user_id][message.channel.id]['emoji'] += 1
                if message.stickers:
                    users[user_id][message.channel.id]['sticker'] += len(message.stickers)
                users[user_id][message.channel.id]['message'] += 1
                
            await text_channel.send(f'{len(history)}, {channel.name}, ready')
        sql = ''
        for key, channel_data in users.items():
            for channel_id, data in channel_data.items():
                sql += f'insert into web_stat_all_stats values (nextval(\'web_stat_all_stats_id_seq\'), {key}, {channel_id}, {data["message"]}, {data["emoji"]}, {data["sticker"]}, {data["image"]}, {data["gif"]}, 0);\n'
        
        print(users)
        self.bot.db.custom_command(sql)

    @commands.is_owner()
    @commands.command()
    async def get(self, ctx):
        guild = await self.bot.fetch_guild(858053936313008129)

        channels = await guild.fetch_channels()

        threads_ids = [
            881983857019191296, 
            957040305222348860,
            889243020707369031,
            932628946443468841,
            870347994669662249,
            880810276981714954,
            895049999228993556,
            875431191245885460,
            931920673297801256,
            873264415368179773,
            941774848886190090
        ]
        threads = []
        for thread_id in threads_ids:
            threads.append(await guild.fetch_channel(thread_id))
        channels += threads

        sql = ''
        for channel in channels:
            try:
                # channel = await guild.fetch_channel(channel)
                print(channel.name)
                sql += f'insert into web_stat_user_data values (nextval(\'web_stat_user_data_id_seq\'), {channel.id}, \'{channel.name}\', \'\', \'\', {True});\n'
            except:
                sql += f'insert into web_stat_user_data values (nextval(\'web_stat_user_data_id_seq\'), {channel}, \'Deleted channel\', \'\', \'\', {False});\n'
        users = await guild.fetch_members(limit=None).flatten()
        # sql = ''
        # for user in users:
        #     sql += f'insert into web_stat_user_data values (nextval(\'web_stat_user_data_id_seq\'), {user.id}, \'{user.name}\', \'{user.display_name}\', \'{user.avatar}\', {True});\n'
        self.bot.db.custom_command(sql)
        await ctx.send('Ready')

    
    @commands.is_owner()
    @commands.command()
    async def pop_words(self, ctx):
        print('start searching')
        guild = await self.bot.fetch_guild(858053936313008129)
        text_channel = await guild.fetch_channel(863966092153192478)

        channels = await guild.fetch_channels()
        # threads = await guild.active_threads()
        

        threads_ids = [881983857019191296, 
            957040305222348860,
            889243020707369031,
            932628946443468841,
            870347994669662249,
            880810276981714954,
            895049999228993556,
            875431191245885460,
            931920673297801256,
            873264415368179773,
            941774848886190090
        ]
        threads = []
        for thread_id in threads_ids:
            threads.append(await guild.fetch_channel(thread_id))
        channels += threads

        word_mes = {}
        emoji_mes = {}
        count_mes = {}
        day_stat = 8
        time = datetime(day=day_stat,month=5,year=2022)
        for i in range(day_stat, 16):
            count_mes[i] = 0

        for channel in channels:

            print(f'start with channel {channel.name}')
            if not (channel.type == discord.ChannelType.text or \
                    channel.type == discord.ChannelType.private or \
                    channel.type == discord.ChannelType.group or \
                    channel.type == discord.ChannelType.public_thread or \
                    channel.type == discord.ChannelType.private_thread):
                continue
            if channel.id == 858278222188773436:
                continue
            messages = await channel.history(limit=None, after=time).flatten()
            print(len(messages))
            for message in messages:
                day = message.created_at.day
                if day < day_stat:
                    continue
                count_mes[day] += 1
                emoji = re.search('(<a?)?:\w+:(\d{18}>)?', message.content)
                if emoji:
                    span = emoji.span()
                    emoji = message.content[span[0]:span[1]]
                    if not emoji in emoji_mes.keys():
                        emoji_mes[emoji] = 0
                    emoji_mes[emoji] += 1

                for word in message.content.split(' '):
                    emoji = re.search('(<a?)?:\w+:(\d{18}>)?', word)
                    if len(word) <= 3 or emoji:
                        continue

                    if not word in word_mes.keys():
                        word_mes[word] = 0
                    word_mes[word] += 1
        
        # print({k: v for k, v in sorted(word_mes.items(), key=lambda item: item[1])})
        print({k: v for k, v in sorted(emoji_mes.items(), key=lambda item: item[1])})
        print(count_mes)
        a = ''
        for k, v in word_mes.items():
            a += ' '.join([k] * v)
            a += ' '
        with open('words.txt', 'w') as f:
            f.write(a)

        await text_channel.send('REady')

                
            # count of messages
            # count of text
            # count of emoji

        








def setup(bot):
    bot.add_cog(Fun(bot))
