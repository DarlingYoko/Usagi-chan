from discord.ext import commands
from discord.commands import SlashCommandGroup

from usagiBot.src.UsagiChecks import check_cog_whitelist, check_correct_channel_command
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError

from usagiBot.cogs.Wordle.wordle_utils import *


class Wordle(commands.Cog):
    def __init__(self, bot):
        pass

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    wordle_game = SlashCommandGroup(
        name="create_wordle_game",
        description="Create new Wordle game!",
        checks=[
            check_correct_channel_command().predicate
        ],
        command_tag="create_wordle_game",
    )

    @wordle_game.command(name="manual", description="Create your own Wordle game!")
    @commands.cooldown(per=60, rate=1, type=commands.BucketType.user)
    @discord.commands.option(
        name="word",
        description="Enter your word!",
        required=True,
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
        word = word.upper()
        for i in word:
            letter_ascii = ord(i)
            if not (65 <= letter_ascii <= 90) and not (1040 <= letter_ascii <= 1071):
                await ctx.respond("Your word contains symbols, pls guess real word.", ephemeral=True)
                return

        if not (4 < len(word) < 11):
            await ctx.respond("Word length is not correct. Use 5 - 10 length.", ephemeral=True)
            return
        await generate_new_wordle_game(ctx, word, "manual")

    @wordle_game.command(name="auto", description="Create auto Wordle game for you!")
    @commands.cooldown(per=60, rate=1, type=commands.BucketType.channel)
    @discord.commands.option(
        name="word_lenght",
        description="Insert how long will be word!",
        autocomplete=lambda x: range(5, 10),
        required=True,
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
        if not (4 < word_lenght < 10):
            await ctx.respond("Word length is not correct. Use 5 - 9 length.", ephemeral=True)
            return
        word = get_word(word_lenght)
        await generate_new_wordle_game(ctx, word, "auto")

    @commands.slash_command(name="rules_wordle", description="How to play Wordle")
    async def wordle_rules(
            self,
            ctx,
    ) -> None:
        """
        Get full rules for Wordle
        :param ctx:
        :return:
        """
        description = (
            f'''```ansi
This is a simple [2;32m[2;33m[2;37m[1;37m[1;37mWordle game[0m[1;37m[0m[2;37m[0m[2;33m[0m[2;32m[0m where you have to guess the hidden word.
You only have the number of letters in a word. 
You can make your guesses and Usagi-chan will give you clues if you guessed the correct letters.

[0;2m[0m[0;2mHint Options
[0;32mGreen [0m— the correct letter in its place
[0;33mYellow [0m— the correct letter is in the wrong place
[0;30mBlack [0m— wrong letter[0m[2;30m[0m

There are two options for guessing the word. [0;2m
You can do[0m[0;2m this by entering your word through the manual creation of the game or 
ask to generate a random word for yourself by the number of letters in it.[0m

[2;31mAll users have a total number of guesses, so, choose your answers thoroughly.[0m
```'''
        )

        embed = get_embed(
            title="Wordle rules",
            description=description,
            footer=["Увы", "https://cdn.discordapp.com/attachments/881532399467528222/1067059467260280934/1063188001263464499.png"],
        )

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Wordle(bot))
