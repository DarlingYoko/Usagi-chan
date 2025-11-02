from discord.ext import commands
from discord.commands import SlashCommandGroup

from usagiBot.src.UsagiChecks import check_cog_whitelist, check_correct_channel_command
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError

from usagiBot.cogs.Wordle.wordle_utils import *

from pycord18n.extension import _


class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    wordle_game = SlashCommandGroup(
        name="wordle_game",
        name_localizations={"ru": "вордли_игра"},
        description="Create new Wordle game!",
        description_localizations={"ru": "Создать новую Вордли игру."},
        checks=[check_correct_channel_command().predicate],
        command_tag="create_wordle_game",
    )

    @wordle_game.command(
        name="manual",
        name_localizations={"ru": "личная"},
        description="Create your own Wordle game!",
        description_localizations={"ru": "Создать свою собственную Вордли игру."},
    )
    @commands.cooldown(per=60, rate=1, type=commands.BucketType.user)
    @discord.commands.option(
        name="word",
        name_localizations={"ru": "слово"},
        description="Enter your word!",
        description_localizations={"ru": "Введите своё слово."},
    )
    async def wordle_manual_game(
        self,
        ctx,
        word: str,
    ) -> None:
        """
        Create manual Wordle game
        :param ctx:
        :param word:
        :return:
        """
        await ctx.defer(ephemeral=True)
        word = word.upper()
        for i in word:
            letter_ascii = ord(i)
            if not (65 <= letter_ascii <= 90) and not (1040 <= letter_ascii <= 1071):
                await ctx.send_followup(
                    _("Your word contains symbols"),
                    ephemeral=True,
                )
                return

        if not (4 < len(word) < 11):
            await ctx.send_followup(_("Word length is not correct"), ephemeral=True)
            return
        lang = self.bot.language.get(ctx.user.id, "en")
        await generate_new_wordle_game(ctx, word, "manual", self.bot, lang)

    @wordle_game.command(
        name="auto",
        name_localizations={"ru": "авто"},
        description="Create auto Wordle game for you!",
        description_localizations={"ru": "Создать авто Вордли игру для себя и друзей."},
    )
    @commands.cooldown(per=60, rate=1, type=commands.BucketType.channel)
    @discord.commands.option(
        name="word_lenght",
        name_localizations={"ru": "длина_слова"},
        description="Insert how long will be word!",
        description_localizations={
            "ru": "Выберите насколько длинное слово загадает вам Усаги."
        },
        choices=map(lambda x: str(x), range(5, 14)),
    )
    async def wordle_auto_game(
        self,
        ctx,
        word_lenght: int,
    ) -> None:
        """
        Create auto Wordle game
        :param ctx:
        :param word_lenght:
        :return:
        """
        await ctx.defer(ephemeral=True)
        word = get_word(word_lenght)
        lang = self.bot.language.get(ctx.user.id, "en")
        await generate_new_wordle_game(ctx, word, "auto", self.bot, lang)

    @commands.slash_command(
        name="rules_wordle",
        name_localizations={"ru": "вордли_правила"},
        description="How to play Wordle",
        description_localizations={"ru": "Как играть в Вордли."},
    )
    async def wordle_rules(
        self,
        ctx,
    ) -> None:
        """
        Get full rules for Wordle
        :param ctx:
        :return:
        """
        description_en = """```ansi
This is a simple [2;32m[2;33m[2;37m[1;37m[1;37mWordle game[0m[1;37m[0m[2;37m[0m[2;33m[0m[2;32m[0m where you have to guess the hidden word.
You only have the number of letters in a word. 
You can make your guesses and Usagi-chan will give you clues if you guessed the correct letters.

[0;2m[0m[0;2mHint Options:
[0;32mGreen [0m— the correct letter in its place
[0;33mYellow [0m— the correct letter is in the wrong place
[0;30mBlack [0m— wrong letter[0m[2;30m[0m

There are two options for guessing the word. [0;2m
You can do[0m[0;2m this by entering your word through the manual creation of the game or 
ask to generate a random word for yourself by the number of letters in it.[0m

[2;31mAll users have a total number of guesses, so, choose your answers thoroughly.[0m
```"""

        description_ru = """```ansi
Это проста [2;32m[2;33m[2;37m[1;37m[1;37mВордли игра[0m[1;37m[0m[2;37m[0m[2;33m[0m[2;32m[0m где вам нужно отгадать загаданное слово.
У вас есть только количество букв в слове. 
Вы можете делать свои предоложения и Усаги-чан даст вам ответ сколько букв вы угадали.

[0;2m[0m[0;2mВарианты подсказок:
[0;32mЗелёный [0m— Правильная буква на своём месте
[0;33mЖёлтый [0m— Правильная буква НЕ на своём месте
[0;30mЧёрный [0m— такой буквы нет[0m[2;30m[0m

Существует два варианта загадать слово.[0;2m
Вы можете [0m[0;2m сами создать игру введя своё слово в личную игру или 
попросить сгенерировать вам рандомное слово от Усаги выбрав только количество букв.[0m

[2;31mВсе пользователи имеют общее число попыток, так что выбирайте ваши ответы с УМОМ.[0m
```"""

        lang = self.bot.language.get(ctx.user.id, "en")
        description = description_en if lang == "en" else description_ru

        embed = get_embed(
            title="Wordle rules",
            description=description,
            footer=[
                "Увы",
                "https://cdn.discordapp.com/attachments/881532399467528222/1067059467260280934/1063188001263464499.png",
            ],
        )

        await ctx.respond(embed=embed)

    @wordle_game.command(
        name="top",
        name_localizations={"ru": "топ"},
        description="View top players in Wordle game.",
        description_localizations={"ru": "Посмотреть список лучших игроков Вордли."},
    )
    @commands.cooldown(per=60, rate=1, type=commands.BucketType.channel)
    async def wordle_top(self, ctx):
        all_results = await UsagiWordleResults.get_all_by(guild_id=ctx.guild.id)
        top_players = sorted(all_results, key=lambda x: x.points, reverse=True)[:10]
        title = _("Top players")
        result = list(
            map(
                lambda x: _("Counter players").format(
                    count=x[0],
                    user_id=x[1].user_id,
                    points=x[1].points,
                    count_of_games=x[1].count_of_games,
                ),
                enumerate(top_players),
            )
        )
        result_text = "\n".join(result)
        embed = get_embed(title=title, description=result_text)
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Wordle(bot))
