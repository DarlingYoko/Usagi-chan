import discord, requests, asyncio, random
from discord.ext import commands
from bin.converters import *
from bin.functions import format_time
from .utils import *


# !create_game <word> ?
# !rules или правила
# !wordle_top - топ игроков по поинтам
#
# Пользователь в лс Усаги пишет команду о создании игры
# Далее Усаги пишет в канал игор, что создана игра №Х
#
# Под каждую игру делать отдельную ветку, чтобы
# не захломлять общий чатик с вопросами.
# Пользователь пишет join X и Усаги его добавляет в ветку для игры,
# где он дальше может угадывать слово. тогда пользователю не надо
# будет писать к какой игре он хочет угадать слово.
# Все пользователи одной игры угадывают вместе и имеют общее число попыток

# Таблица рейтинга:
# За победу юзер получает кол-во очков в зависимости от количества слов.
# Слово из 5 букв -> 6 попыток -> макс поинты = 6
# 1\6 слово - 6 поинтов
# топ по количеству отгаданых слов
# ...
# ты можешь по юникоду букв узнавать это ру или англ и дописывать к усаги
# вопрос повторяющихся буков удалять когда нахожу букву чтобы не было некст буквы

# надо команду для закрытия.
# ограничение кол-ва букв до 7
# просто тегать создателя а не писать
# + по другому оформление хп

# из улучшений можно после завершения игры писать сюда резалт, а то листать до треда который создан давно неудобно
# проверка циферок
# два варика игор
# как то фиксануть одновременный ответ

# eng upper 65-90
# ru upper 1040-1071

# разобраться с выделением буков





class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    @commands.command(help = 'dm')
    @commands.dm_only()
    @commands.cooldown(per=30, rate=1)
    async def create_game(self, ctx, word: str):
        token = 'dict.1.1.20220122T123122Z.47e058e705292d75.744c1f19b19a4e0f60f785e76931856d74b3c1b5'
        # return await ctx.send(f'Игры временно приостановленны, пока идёт оптимизация.')
        word = word.upper()
        type = 'расширенная'
        # проверка на реальность слова
        lang = ''
        first_letter = ord(word[0])
        if first_letter >= 65 and first_letter <= 90:
            lang = 'en'
        if first_letter >= 1040 and first_letter <= 1071:
            lang = 'ru'
        url = f'https://dictionary.yandex.net/api/v1/dicservice.json/lookup?key={token}&lang={lang}-{lang}&text='
        r = requests.get(url + word)

        data = r.json()
        if 'def' in data.keys() and data['def']:
            if data['def'][0]['text'].upper() == word:
                if len(word) <= 7 and len(word) >= 2:
                    type = 'обычная'

        if type == 'расширенная':
            await ctx.send('Я не нашла это слово в словарике или оно больше 7 буков, хочешь создать расширенную версию игры?\nДа/Нет (Yes/No)')
            def check(res):
                return res.channel == ctx.channel and res.author == ctx.author

            try:
                message = await ctx.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return await ctx.send('Ты не успел ответить за отведённое время. БЫБЫ')

            answer = message.content


            if answer.lower() in ['да', 'д', 'yes', 'y']:
                await ctx.send('Хорошо, создаю расширенную версию игры.')

            else:
                return await ctx.send('Хорошо, тогда выбери другое слово для игры, мяу.')


        language = 'русских' if lang == 'ru' else 'английских'
        last_id = self.bot.db.get_value('wordle', 'winner_id', 'id', 0) + 1
        channel = await self.bot.fetch_channel(self.config['channel']['wordle'])
        thread_name = f'Wordle Game #{last_id}'
        message = f'''#Новая __**{type}**__ игра от {ctx.author.mention}. <a:BasedgePooPoo:933131389526757476>
Слово состоит из **{len(word)}** {language} буковок. <:StaregeNoted:860038779070447667>

У вас только **{len(word) + 1}** попыток, пришло время их тратить! <a:sparkles:934435764564013076>'''
        type = discord.ChannelType.public_thread
        lives = len(word) + 1
        thread = await channel.create_thread(name=thread_name, type=type, auto_archive_duration=1440)

        await thread.send(message)
        await ctx.send(f'Ваша игра создана -> {thread.mention}')
        await thread.add_user(ctx.author)

        self.bot.db.insert('wordle', last_id, 0, 0, thread.id, word, lives, ctx.author.id, '', lang , '', '', False)
        self.bot.db.update('wordle', 'winner_id', 'id', last_id, 0)


    @commands.command(aliases = ['ответ'])
    @commands.cooldown(per=10, rate=1, type=commands.BucketType.channel)
    async def answer(self, ctx, try_word: str):
        try_word = list(try_word.upper())
        command = f'SELECT word,lives,owner_id,lang,ban_words,white_words,try_words,dababy_game from wordle where channel_id = {ctx.channel.id};'
        # word = self.bot.db.get_value('wordle', 'word', 'channel_id', ctx.channel.id)
        # lives = self.bot.db.get_value('wordle', 'lives', 'channel_id', ctx.channel.id)
        # author_id = self.bot.db.get_value('wordle', 'owner_id', 'channel_id', ctx.channel.id)
        # lang = self.bot.db.get_value('wordle', 'lang', 'channel_id', ctx.channel.id)
        # ban_words_db = self.bot.db.get_value('wordle', 'ban_words', 'channel_id', ctx.channel.id)
        result = self.bot.db.custom_command(command)
        if not result:
            return
        result = result[0]
        word = result[0]
        lives = result[1]
        author_id = result[2]
        lang = result[3]
        ban_words_db = result[4]
        white_words_db = result[5]
        try_words_db = result[6]
        dababy_game = result[7]
        wordle_channel_id = self.config['channel'].getint('wordle')
        wordle_channel = await ctx.bot.fetch_channel(wordle_channel_id)
        if not word:
            # wrong channel
            return await ctx.send(f'{ctx.author.mention}, В этом канале не играють.')
        word = list(word)

        if ctx.author.id == author_id:
            # owner answered
            return await ctx.send(f'{ctx.author.mention}, Ты загадал слово, тебе низя отгадывать!')

        if len(try_word) != len(word):
            # wrong length
            return await ctx.send(f'{ctx.author.mention}, Дурак? Длина слова другая!')

        if dababy_game:
            check = check_word(''.join(word))
            if not check:
                return await ctx.send(f'{ctx.author.mention}, Такого слова нет в словаре <a:Tssk:883736146578915338>')

        blocks = {}
        word_copy = word.copy()
        false_pos = 'yellow_block'
        not_exist = 'black_block'
        true_pos = 'green_block'
        ban_words = []
        white_words = []
        try_words = []
        counter = 0
        for i in range(len(word)):
            if try_word[i] == word[i]:
                blocks[i] = true_pos
                word_copy.remove(try_word[i])
                counter += 1
                white_words.append(try_word[i])

        for i in range(len(word)):
            if try_word[i] in word_copy and i not in blocks.keys():
                blocks[i] = false_pos
                word_copy.remove(try_word[i])
                try_words.append(try_word[i])

        for i in range(len(word)):
            if i not in blocks.keys():
                blocks[i] = not_exist
                ban_words.append(try_word[i])

        file = create_pic_from_word(blocks, try_word)

        if ban_words_db:
            ban_words_db = ban_words_db.split(',')
        else:
            ban_words_db = []

        if white_words_db:
            white_words_db = white_words_db.split(',')
        else:
            white_words_db = []

        if try_words_db:
            try_words_db = try_words_db.split(',')
        else:
            try_words_db = []
        winner_text = ''
        default_text = ''
        if dababy_game:
            try_dababy = (len(try_words) - len(set(try_words) & set(try_words_db)))
            white_dababy = (len(white_words) - len(set(white_words) & set(white_words_db))) * 2
            winner_text = f' И заработал {len(word) * 5} <:dababy:915736432021221386> за угаданное слово!'
            default_text = f', Ты открыл новые буквы и заработал {try_dababy + white_dababy} <:dababy:915736432021221386>!'
        ban_words = list(set(ban_words + ban_words_db))
        white_words = list(set(white_words + white_words_db))
        try_words = list(set(try_words + try_words_db))

        await ctx.send(f'{ctx.author.mention}', file=file)

        if counter == len(word):
            # win!
            word = ''.join(word)
            await ctx.send(f'{ctx.author.mention}, Ула Ула ты победил! {winner_text}')
            self.bot.db.custom_command(f'update wordle set winner_id = {ctx.author.id}, points = {lives} where channel_id = {ctx.channel.id};\n' +\
                                        f'update pivo set money = money + {len(word) * 5} where user_id = {ctx.author.id};')
            await wordle_channel.send(f"<@{author_id}>\n```cs\n# {ctx.channel.name} закончена.\nПобедитель — {ctx.author.name}\nСлово — '{word}'```")
            return await ctx.channel.edit(archived=True, locked=True)

        lives -= 1
        if lives == 0:
            # end game
            word = ''.join(word)
            await ctx.send(f'Слово никто не угадал(\nПравильное слово было - **{word}**')
            await wordle_channel.send(f"<@{author_id}>\n```cs\n# {ctx.channel.name} закончена.\nНикто не отгадал слово '{word}'```")
            return await ctx.channel.edit(archived=True, locked=True)


        await ctx.send(f'Ваше текущее количество попыток - {lives}.\n{ctx.author.mention} {default_text}', file=get_words_keybord(ban_words, white_words, try_words, lang))
        self.bot.db.custom_command(f'update wordle set lives = {lives}, ban_words = \'{",".join(ban_words)}\', white_words = \'{",".join(white_words)}\', try_words = \'{",".join(try_words)}\'  where channel_id = {ctx.channel.id};')
        if dababy_game:
            self.bot.db.custom_command(f'update pivo set money = money + {try_dababy + white_dababy} where user_id = {ctx.author.id};')


    @commands.command(aliases = ['вордли_топ', 'вордле_топ', 'топ_вордле', 'топ_вордли', 'top_wordle'],
                        help='wordle',
                        )
    @commands.cooldown(per=60, rate=1)
    async def wordle_top(self, ctx):
        all_wordle = self.bot.db.get_all('wordle')

        winners = {}
        for wordle in all_wordle:
            game_id = wordle[0]
            winner_id = wordle[1]
            if game_id == 0 or winner_id == 0:
                continue
            winner = ctx.guild.get_member(winner_id)
            points = wordle[2]
            if not winner:
                name = f'<@{winner_id}>'
            else:
                name = winner.name
            if name in winners.keys():
                winners[name] += points
            else:
                winners[name] = points

        answer = f'```cs\n# Топ игроков в Wordle Usagi-chan edition\n'
        counter = 1
        winners = {k: v for k, v in sorted(winners.items(), key=lambda item: item[1], reverse=True)}
        for key, value in winners.items():
            # print(key)
            answer += f'{counter}. {key} ---- {value} Очков.\n'
            counter += 1
        answer += '```'
        await ctx.send(answer)


    @commands.command(aliases = ['правила_вордли'])
    async def rules_wordle(self, ctx):
        await ctx.send(f'Все правила расписанны туть -> https://ptb.discord.com/channels/858053936313008129/934086248245637212/934186880323424366')


    @commands.cooldown(per=60, rate=1)
    @commands.command(aliases = ['топ_слов'])
    async def dif_top(self, ctx):
        all_wordle = self.bot.db.get_all('wordle')

        winners = {}

        for wordle in all_wordle:
            game_id = wordle[0]
            winner_id = wordle[1]
            if game_id == 0 or winner_id == 0:
                continue
            winner = ctx.guild.get_member(winner_id)
            points = wordle[2]
            if not winner:
                name = f'<@{winner_id}>'
            else:
                name = winner.name
            if points:
                if name in winners.keys():
                    winners[name] += 1
                else:
                    winners[name] = 1

        answer = f'```cs\n# Топ игроков в Wordle Usagi-chan edition\n'
        counter = 1
        winners = {k: v for k, v in sorted(winners.items(), key=lambda item: item[1], reverse=True)}
        for key, value in winners.items():
            # print(key)
            answer += f'{counter}. {key} ---- {value} слов.\n'
            counter += 1
        answer += '```'
        await ctx.send(answer)

    @commands.command(help = 'wordle', aliases = ['авто_игра'])
    @commands.cooldown(per=60, rate=1)
    async def auto_game(self, ctx, count_of_letters: int = None):

        if not count_of_letters or count_of_letters < 4 or count_of_letters > 12:
            await ctx.send(f'{ctx.author.mention}, Ищу рандомное слово, ы. Dababy')
            count_of_letters = random.randint(4, 12)
        word = get_word(count_of_letters)
        if not word:
            return await ctx.send(f'{ctx.author.mention}, Не получилось найти слово, попробуй ещё раз!')
        last_id = self.bot.db.get_value('wordle', 'winner_id', 'id', 0) + 1
        channel = await self.bot.fetch_channel(self.config['channel']['wordle'])
        thread_name = f'Wordle Game #{last_id}'
        dababy_game = False
        dababy_text = ''
        if 5 <= count_of_letters <= 7:
            dababy_game = True
            dababy_text = '**За эту игру можно получить дабаби!**'
        message = f'''#Новая __**обычная**__ игра от Меня для {ctx.author.mention}. <a:BasedgePooPoo:933131389526757476>
Слово состоит из **{len(word)}** русских буковок. <:StaregeNoted:860038779070447667>

У вас только **{len(word) + 1}** попыток, пришло время их тратить! <a:sparkles:934435764564013076>
{dababy_text}'''
        type = discord.ChannelType.public_thread
        lives = len(word) + 1
        thread = await channel.create_thread(name=thread_name, type=type, auto_archive_duration=1440)

        await thread.send(message)
        await ctx.send(f'Ваша игра создана -> {thread.mention}')

        self.bot.db.insert('wordle', last_id, 0, 0, thread.id, word, lives, 801153197552304129, '', 'ru', '', '', dababy_game)
        self.bot.db.update('wordle', 'winner_id', 'id', last_id, 0)

    @create_game.error
    async def create_game_errors(self, ctx, error):
        if isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(f'{ctx.author.mention} Эта команда только для лс! Баака')
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.mention} Ты не ввёл слово для игры.')
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            time = format_time(retry_after)
            await ctx.send(f'{ctx.author.mention} Пока рано для новой игры, подожди чуток.\n Попробуй через {time}')

    @answer.error
    async def answer_errors(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            time = format_time(retry_after)
            await ctx.send(f'{ctx.author.mention} Пока рано для ответа, подожди чуток.\n Попробуй через {time}')

    @auto_game.error
    async def auto_game_errors(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            time = format_time(retry_after)
            await ctx.send(f'{ctx.author.mention} Пока рано для новой игры, подожди чуток.\n Попробуй через {time}')

    @wordle_top.error
    async def wordle_top_errors(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            time = format_time(retry_after)
            await ctx.send(f'{ctx.author.mention} Пока рано для нового топа, подожди чуток.\n Попробуй через {time}')


def setup(bot):
    bot.add_cog(Wordle(bot))
