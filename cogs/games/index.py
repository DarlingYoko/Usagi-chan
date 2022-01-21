import discord
from discord.ext import commands, tasks
from bin.converters import *
from bin.functions import get_embed
from .utils import create_pic_from_word


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
# ...






class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    @commands.command(help = 'dm')
    @commands.dm_only()
    async def create_game(self, ctx, word: str):
        last_id = self.bot.db.get_value('wordle', 'winner_id', 'id', 0) + 1
        channel = await self.bot.fetch_channel(self.config['channel']['wordle'])
        thread_name = f'Wordle Game #{last_id}'
        message = 'New Game Starts!\n'+ '⬜' * len(word) + '\nGL HF!'
        type = discord.ChannelType.public_thread
        word = word.upper()
        lives = len(word) + 1
        thread = await channel.create_thread(name=thread_name, type=type, auto_archive_duration=60)
        await thread.send(message)
        await thread.send(f'Общее число жизней для этого слова - {lives} ❤️\nСлово из {len(word)} букв.\nСлово загадал {ctx.author.name}')
        await ctx.send(f'Ваша игра создана -> {thread.mention}')
        await thread.add_user(ctx.author)

        self.bot.db.insert('wordle', last_id, 0, 0, thread.id, word, lives, ctx.author.id)
        self.bot.db.update('wordle', 'winner_id', 'id', last_id, 0)


    @commands.command(aliases = ['ответ'])
    async def answer(self, ctx, try_word: str):
        try_word = try_word.upper()
        word = self.bot.db.get_value('wordle', 'word', 'channel_id', ctx.channel.id)
        lives = self.bot.db.get_value('wordle', 'lives', 'channel_id', ctx.channel.id)
        author_id = self.bot.db.get_value('wordle', 'owner_id', 'channel_id', ctx.channel.id)
        if not word:
            # wrong channel
            return await ctx.send(f'{ctx.author.mention}, В этом канале не играють.')

        if ctx.author.id == author_id:
            # owner answered
            return await ctx.send(f'{ctx.author.mention}, Ты загадал слово, тебе низя отгадывать!')

        if len(try_word) != len(word):
            # wrong length
            return await ctx.send(f'{ctx.author.mention}, Дурак? Длина слова другая!')

        blocks = []
        false_pos = 'yellow_block'
        not_exist = 'black_block'
        true_pos = 'green_block'

        for i in range(len(word)):
            if try_word[i] == word[i]:
                blocks.append(true_pos)
            elif try_word[i] in word:
                blocks.append(false_pos)
            else:
                blocks.append(not_exist)

        file = create_pic_from_word(blocks, try_word)

        await ctx.send(f'{ctx.author.mention}', file=file)

        if try_word == word:
            # win!
            await ctx.send(f'Ула Ула ты победил!')
            self.bot.db.update('wordle', 'winner_id', 'channel_id', ctx.author.id, ctx.channel.id)
            self.bot.db.update('wordle', 'points', 'channel_id', lives, ctx.channel.id)
            return await ctx.channel.edit(archived=True, locked=True)

        lives -= 1
        if lives == 0:
            # end game
            await ctx.send(f'Слово никто не угадал(\nПравильное слово было - **{word}**')
            return await ctx.channel.edit(archived=True, locked=True)


        await ctx.send(f'Ваше текущее количество жизней - {lives} ❤️')

        self.bot.db.update('wordle', 'lives', 'channel_id', lives, ctx.channel.id)


    @commands.command(aliases = ['вордли_топ', 'вордле_топ', 'топ_вордле', 'топ_вордли', 'top_wordle'],
                        help='wordle',
                        )
    async def wordle_top(self, ctx):
        all_wordle = self.bot.db.get_all('wordle')

        winners = {}

        for wordle in all_wordle:
            game_id = wordle[0]
            if game_id == 0:
                continue
            winner_id = wordle[1]
            winner = ctx.guild.get_member(winner_id)
            points = wordle[2]
            if winner in winners.keys():
                winners[winner] += points
            else:
                winners[winner] = points

        answer = f'```cs\n# Топ игроков в Wordle Usagi-chan edition\n'
        counter = 1
        winners = {k: v for k, v in sorted(winners.items(), key=lambda item: item[1], reverse=True)}
        for key, value in winners.items():
            answer += f'{counter}. {key.name} ---- {value} Очков.\n'
            counter += 1
        answer += '```'
        await ctx.send(answer)





    @create_game.error
    async def create_game_errors(self, ctx, error):
        if isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(f'{ctx.author.mention} Эта команда только для лс! Баака')
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.mention} Ты не ввёл слово для игры.')




def setup(bot):
    bot.add_cog(Games(bot))
