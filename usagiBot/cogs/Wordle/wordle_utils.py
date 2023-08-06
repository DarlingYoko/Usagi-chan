from more_itertools import locate

import discord
import random

from easy_pil import Editor
from PIL import Image, ImageFont
from discord import File

from usagiBot.env import BOT_ID
from usagiBot.db.models import UsagiWordleGames, UsagiWordleResults
from usagiBot.src.UsagiUtils import get_embed

from pycord18n.extension import _


class WordleAnswer(discord.ui.Modal):
    def __init__(self, game, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.letter_blocks = None
        self.game = game
        self.add_item(
            discord.ui.InputText(
                label=self.game.bot.i18n.get_text("Answer", self.game.user_lang),
                max_length=len(game.word),
                min_length=len(game.word),
            )
        )
        # self.add_item(discord.ui.InputText(label="Long Input", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        """
        Check answer and regenerate embed with image
        :param interaction:
        :return:
        """
        answer = self.children[0].value.upper()
        if self.game.owner_id == int(BOT_ID):
            check_reality = check_word_for_reality(answer)
            if not check_reality:
                await interaction.response.send_message(
                    self.game.bot.i18n.get_text("This word is not in the dictionary", self.game.user_lang),
                    ephemeral=True,
                )
                return

        for i in answer:
            letter_ascii = ord(i)
            if not (65 <= letter_ascii <= 90) and not (1040 <= letter_ascii <= 1071) and i != "Ё":
                await interaction.response.send_message(
                    self.game.bot.i18n.get_text("Your word contains symbols", self.game.user_lang),
                    ephemeral=True
                )
                return

        self.letter_blocks = [""] * len(self.game.word)
        self.game.lives_count -= 1

        for letter in list(set(answer)):
            correct_indices = set(locate(self.game.word, lambda x: x == letter))
            guessed_indices = set(locate(answer, lambda x: x == letter))
            guessed_letters = correct_indices & guessed_indices
            difference_letters = guessed_indices - correct_indices

            new_green_indices = list(guessed_letters)
            new_yellow_indices = list(difference_letters)[
                : len(correct_indices) - len(new_green_indices)
            ]
            new_black_indices = list(difference_letters - set(new_yellow_indices))

            new_green_letters = list(map(lambda x: answer[x], new_green_indices))
            new_yellow_letters = list(map(lambda x: answer[x], new_yellow_indices))
            new_black_letters = list(map(lambda x: answer[x], new_black_indices))

            for i in new_green_indices:
                self.letter_blocks[i] = "green_block"

            for i in new_yellow_indices:
                self.letter_blocks[i] = "yellow_block"

            for i in new_black_indices:
                self.letter_blocks[i] = "black_block"

            self.game.green_letters = self.game.green_letters + new_green_letters
            self.game.yellow_letters = self.game.yellow_letters + new_yellow_letters
            self.game.black_letters = self.game.black_letters + new_black_letters

        wordle_image = create_full_wordle_pic(
            word=answer,
            lang=self.game.word_language,
            lives_count=self.game.lives_count,
            game_id=self.game.game_id,
            blocks=self.letter_blocks,
            green_letters=self.game.green_letters,
            yellow_letters=self.game.yellow_letters,
            black_letters=self.game.black_letters,
            prev_pic=self.game.image,
        )
        embed = get_embed(
            title=self.game.embed.title,
            description=self.game.embed.description,
            url_image=f"attachment://Usagi_wordle_game_{self.game.game_id}_{self.game.lives_count}.png",
        )
        self.game.embed = embed
        self.game.image = wordle_image
        await interaction.response.edit_message(embed=embed, file=wordle_image)

        if answer == self.game.word.upper():
            # win condition ctx, result, word, game_author
            await end_game(
                interaction=interaction,
                result="win",
                word=self.game.word,
                lives_count=self.game.lives_count,
                game=self.game,
            )
        elif self.game.lives_count == 0:
            # lose condition
            await end_game(
                interaction=interaction,
                result="lose",
                word=self.game.word,
                game=self.game,
            )


class WordleGame(discord.ui.View):
    def __init__(
        self,
        embed: discord.Embed,
        word: str,
        owner_id: int,
        word_language: str,
        lives_count: int,
        game_id: int,
        timeout: int,
        bot,
        user_lang: str,
    ):
        super().__init__(timeout=timeout)
        self.embed = embed
        self.word = word
        self.owner_id = owner_id
        self.word_language = word_language
        self.lives_count = lives_count
        self.game_id = game_id
        self.image = None
        self.blocks = []
        self.green_letters = []
        self.yellow_letters = []
        self.black_letters = []
        self.prev_pic_url = None
        self.bot = bot
        self.user_lang = user_lang

    @discord.ui.button(
        label="Guess",
        style=discord.ButtonStyle.primary,
    )
    async def guess_button(self, button, interaction):
        """
        Answer for game
        :param button:
        :param interaction:
        :return:
        """
        if interaction.user.id == self.owner_id:
            # the owner answered
            await interaction.response.send_message(
                self.bot.i18n.get_text("You guessed a word", self.user_lang), ephemeral=True
            )
            return
        await interaction.response.send_modal(
            WordleAnswer(
                game=self,
                title=self.bot.i18n.get_text("Your answer", self.user_lang)
            )
        )


async def generate_new_wordle_game(
    ctx: discord.ApplicationContext,
    word: str,
    game_type: str,
    bot,
    user_lang: str,
) -> None:
    """
    Create a new game with params
    :param ctx: Application Context
    :param word: Word for game
    :param game_type: manual or auto game
    :param bot: bot instanse
    :param user_lang: user language
    :return:
    """
    game_by = _("by") if game_type == "manual" else _("for")
    owner_id = ctx.author.id if game_type == "manual" else int(BOT_ID)

    first_letter = ord(word[0].upper())
    word_language = "russian" if user_lang == "en" else "русском"
    if 65 <= first_letter <= 90:
        word_language = "english" if user_lang == "en" else "английском"

    lives_count = len(word) + 1
    last_obj = await UsagiWordleGames.get_last_obj()
    if last_obj:
        last_id = last_obj.id + 1
    else:
        last_id = 1

    description_en = f"""<a:sparkles:934435764564013076><a:sparkles:934435764564013076>
**Game #{last_id}** created {game_by} <@{ctx.author.id}>.
```ansi
[2;30m[0m[0;2mThe word contains — [0;36m{len(word)}[0m letters.
In {word_language} language.
You have only [0;36m{lives_count}[0m tries and it's time to spend it![0m
```
<a:sparkles:934435764564013076><a:sparkles:934435764564013076>"""

    description_ru = f"""<a:sparkles:934435764564013076><a:sparkles:934435764564013076>
**Игра #{last_id}** создана {game_by} <@{ctx.author.id}>.
```ansi
[2;30m[0m[0;2mСлово содержит — [0;36m{len(word)}[0m букв.
На {word_language} языке.
У вас есть только [0;36m{lives_count}[0m попыток и сейчас самое время их тратить![0m
```
<a:sparkles:934435764564013076><a:sparkles:934435764564013076>"""

    description = description_en if user_lang == "en" else description_ru

    wordle_image = create_full_wordle_pic(
        word=word,
        lang=word_language,
        lives_count=lives_count,
        game_id=last_id,
    )
    embed = get_embed(
        title=_("New Wordle game"),
        description=description,
        url_image=f"attachment://Usagi_wordle_game_{last_id}_{lives_count}.png",
    )

    thread_name = _("Wordle Game last_id").format(last_id=last_id)
    thread_type = discord.ChannelType.public_thread
    thread = await ctx.channel.create_thread(
        name=thread_name, type=thread_type, auto_archive_duration=1 * 60 * 24 * 3
    )

    await thread.add_user(ctx.author)
    try:
        message = await thread.send(
            embed=embed,
            file=wordle_image,
            view=WordleGame(
                embed=embed,
                word=word,
                owner_id=owner_id,
                word_language=word_language,
                lives_count=lives_count,
                game_id=last_id,
                timeout=60 * 60,
                bot=bot,
                user_lang=user_lang,
            ),
        )
        await message.pin(reason="Pin new game")
        await UsagiWordleGames.create(
            guild_id=ctx.guild.id,
            word=word,
            owner_id=owner_id,
            thread_id=thread.id,
        )
    except discord.ApplicationCommandInvokeError as e:
        ctx.bot.logger.error(e)

    await ctx.send_followup(_("Your game was created thread").format(thread=thread.mention), ephemeral=True)


def get_word(length: int) -> str | None:
    """
    Return random word from dict with specified length
    :param length: Length of word
    :return: New word
    """
    with open("./usagiBot/files/dicts/russian.txt", "r", encoding="utf8") as f:
        words = f.readline().split(",")

    words = list(filter(lambda x: len(x) == length, words))
    if not words:
        return None
    word = words[random.randint(0, len(words))]

    return word.upper()


def check_word_for_reality(word: str) -> bool:
    """
    Checks if word in the dictionaries of proof
    :param word: Word to check
    :return: Boolean
    """
    word_upper = word.upper()
    with open("./usagiBot/files/dicts/check_ru_dict.txt", "r", encoding="utf8") as f:
        words = f.readline().split(",")
    return word_upper in words


def create_pic_for_answer(word: str, blocks: list[str]) -> Editor:
    """
    Generate colored image for input word
    :param word: Word
    :param blocks: Colors for word
    :return: New word image
    """
    green_block = Image.open("./usagiBot/files/photo/wordle/green_block.png").resize(
        (153, 153)
    )
    yellow_block = Image.open("./usagiBot/files/photo/wordle/yellow_block.png").resize(
        (153, 153)
    )
    black_block = Image.open("./usagiBot/files/photo/wordle/black_block.png").resize(
        (153, 153)
    )
    color_blocks = {
        "green_block": green_block,
        "yellow_block": yellow_block,
        "black_block": black_block,
    }
    background = Editor(Image.new("RGBA", (173 * len(blocks), 153), (0, 0, 0, 0)))
    font = ImageFont.truetype(font="./usagiBot/files/fonts/genshin.ttf", size=120)

    for i in range(len(blocks)):
        background.paste(color_blocks[blocks[i]], (173 * i, 0))
        if word[i] in "ЙЁ":
            background.text((173 * i + 30, 15), word[i], font=font, color="#fff")
        elif word[i] in "ШЖЩФЫ":
            background.text((173 * i + 15, 30), word[i], font=font, color="#fff")
        else:
            background.text((173 * i + 30, 30), word[i], font=font, color="#fff")

    return background


def create_pic_for_keyboard(
    green_letters: list[str],
    yellow_letters: list[str],
    black_letters: list[str],
    lang: str,
) -> Editor:
    """
    Generate colored keyboard for input letters
    :param green_letters:
    :param yellow_letters:
    :param black_letters:
    :param lang:
    :return: New keyboard image
    """
    font = ImageFont.truetype(font="./usagiBot/files/fonts/genshin.ttf", size=60)
    green_block = Image.open("./usagiBot/files/photo/wordle/green_block.png")
    yellow_block = Image.open("./usagiBot/files/photo/wordle/yellow_block.png")
    black_block = Image.open("./usagiBot/files/photo/wordle/black_block.png")

    ru_keyboard = "ё й ц у к е н г ш щ з х ъ,ф ы в а п р о л д ж э,я ч с м и т ь б ю"
    en_keyboard = "q w e r t y u i o p,a s d f g h j k l,z x c v b n m"

    if lang == "russian":
        keyboard = ru_keyboard.upper()
        blank = Editor("./usagiBot/files/photo/wordle/clear_keyboard.png")
        shift = 113
        layer_counter_place = {0: 0, 1: 1, 2: 2}
    else:
        keyboard = en_keyboard.upper()
        blank = Editor("./usagiBot/files/photo/wordle/clear_keyboard_en.png")
        shift = 57
        layer_counter_place = {0: 0, 1: 1, 2: 3}

    layer_counter = 0

    for layer in keyboard.split(","):
        place_counter = 0
        for letter in layer.split(" "):
            block = None
            color = "#fff"
            if letter in green_letters:
                block = green_block
            elif letter in yellow_letters:
                block = yellow_block
            elif letter in black_letters:
                block = black_block
                color = "#818384"
            if block:
                blank.paste(
                    image=block,
                    position=(
                        113 * place_counter
                        + shift * layer_counter_place[layer_counter],
                        118 * layer_counter,
                    ),
                )
            up = 30
            left = 25
            if letter in "ЙЁ":
                up = 15
            if letter in "ШЖЩФЫ":
                left = 20
            blank.text(
                position=(
                    113 * place_counter
                    + left
                    + shift * layer_counter_place[layer_counter],
                    118 * layer_counter + up,
                ),
                text=letter,
                font=font,
                color=color,
            )
            place_counter += 1
        layer_counter += 1

    return blank


def create_blank_words(length: int) -> Editor:
    """
    Generate blank words places
    :param length:
    :return:
    """
    blank_block = Image.open("./usagiBot/files/photo/wordle/blank_block.png").resize(
        (153, 153)
    )
    background = Editor(
        Image.new("RGBA", (173 * length + 1600, 173 * (length + 1)), (0, 0, 0, 0))
    )
    for i in range(length + 1):
        for j in range(length):
            background.paste(blank_block, (173 * j, 173 * i))
    return background


def create_full_wordle_pic(
    word: str,
    lang: str,
    lives_count: int,
    game_id: int,
    blocks: list[str] = [],
    green_letters: list[str] = [],
    yellow_letters: list[str] = [],
    black_letters: list[str] = [],
    prev_pic: File = None,
) -> File:
    """
    Generate full image with guessed words and kyeboard
    :return: New image
    """
    # If new image -> generate full blank
    length = len(word)
    word_x_pos = length - lives_count
    word_pic = create_pic_for_answer(word, blocks)
    keyboard_pic = create_pic_for_keyboard(
        green_letters, yellow_letters, black_letters, lang
    )
    if prev_pic is None:
        background = create_blank_words(length)
    else:
        prev_img = Image.open(prev_pic.fp)
        background = Editor(prev_img.resize((173 * length + 1600, 173 * (length + 1))))

    background.paste(word_pic, (0, 173 * word_x_pos))
    background.paste(keyboard_pic, (173 * length + 50, 86 * length))

    file = File(
        fp=background.image_bytes,
        filename=f"Usagi_wordle_game_{game_id}_{lives_count}.png",
    )
    return file


async def create_finish_game_embed(
    interaction: discord.Interaction,
    result: str,
    word: str,
    game,
) -> discord.Embed:
    """
    Generate embed with finish info for wordle game
    :param game:
    :param interaction: Interaction
    :param result: result of game
    :param word: Guessed word
    :return: Embed with finished game
    """
    game_author = await interaction.guild.fetch_member(game.owner_id)
    if result == "win":
        winner = interaction.user.name
    else:
        winner = game.bot.i18n.get_text("No one", game.user_lang)

    title = game.bot.i18n.get_text("Wordle Game finished", game.user_lang).format(game=game.game_id)
    description_en = f"""```ansi
[0;2m[0m[0;2mWinner — {winner}[0m[2;32m[0m
[0;2mWord — [0;32m[0;34m[0;36m[0;34m[0;32m[0;35m{word.upper()}[0m[0;32m[0m[0;34m[0m[0;36m[0m[0;34m[0m[0;32m[0m
Created by {game_author.name}#{game_author.discriminator}[0m[2;32m[4;32m[4;32m[0;32m[0m[4;32m[0m[4;32m[0m[2;32m[0m
```"""
    description_ru = f"""```ansi
[0;2m[0m[0;2mПобедитель — {winner}[0m[2;32m[0m
[0;2mСлово — [0;32m[0;34m[0;36m[0;34m[0;32m[0;35m{word.upper()}[0m[0;32m[0m[0;34m[0m[0;36m[0m[0;34m[0m[0;32m[0m
Создана {game_author.name}#{game_author.discriminator}[0m[2;32m[4;32m[4;32m[0;32m[0m[4;32m[0m[4;32m[0m[2;32m[0m
```"""
    description = description_en if game.user_lang == "en" else description_ru

    embed = get_embed(
        title=title,
        description=description,
    )
    return embed


async def end_game(
    interaction: discord.Interaction,
    result: str,
    word: str,
    game,
    lives_count: int = 0,
) -> None:
    """
    Last step when the game finished, update data and notify the winner.
    :param game:
    :param interaction: Interaction
    :param result: result of game
    :param word: Guessed word
    :param lives_count: How many lives left
    :return:
    """
    wordle_channel = interaction.channel.parent
    finish_game_embed = await create_finish_game_embed(
        interaction, result, word, game
    )

    wordle_gamer = await UsagiWordleResults.get(
        guild_id=interaction.guild.id, user_id=interaction.user.id
    )
    if wordle_gamer:
        await UsagiWordleResults.update(
            id=wordle_gamer.id,
            points=wordle_gamer.points + lives_count,
            count_of_games=wordle_gamer.count_of_games + 1,
        )
    else:
        last_game = await UsagiWordleResults.get_last_obj()
        await UsagiWordleResults.create(
            id=last_game.id + 1,
            guild_id=interaction.guild.id,
            user_id=interaction.user.id,
            points=lives_count,
            count_of_games=1,
        )

    await wordle_channel.send(embed=finish_game_embed)
    await interaction.channel.edit(archived=True, locked=True)
