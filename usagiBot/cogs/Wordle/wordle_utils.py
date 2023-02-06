import discord
import random

from easy_pil import Editor
from PIL import Image, ImageFont
from discord import File

from usagiBot.env import BOT_ID
from usagiBot.db.models import UsagiWordleGames, UsagiWordleResults
from usagiBot.src.UsagiUtils import get_embed


class WordleAnswer(discord.ui.Modal):
    def __init__(self, game, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(
            discord.ui.InputText(
                label="Answer",
                max_length=len(game.word),
                min_length=len(game.word),
            )

        )
        self.game = game
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
                    "This word is not in the dictionary <a:Tssk:883736146578915338>",
                    ephemeral=True
                )
                return

        for i in answer:
            letter_ascii = ord(i)
            if not (65 <= letter_ascii <= 90) and not (1040 <= letter_ascii <= 1071):
                await interaction.response.send_message(
                    "Your word contains symbols, pls guess real word.",
                    ephemeral=True
                )
                return

        green_letters = []
        yellow_letters = []
        black_letters = []
        letter_blocks = []
        self.game.lives_count -= 1

        for i in range(len(answer)):
            if answer[i] == self.game.word[i]:
                green_letters.append(answer[i])
                letter_blocks.append("green_block")
            elif answer[i] in self.game.word:
                if yellow_letters.count(answer[i]) < self.game.word.count(answer[i]):
                    yellow_letters.append(answer[i])
                    letter_blocks.append("yellow_block")
                else:
                    letter_blocks.append("black_block")
            else:
                black_letters.append(answer[i])
                letter_blocks.append("black_block")

        self.game.green_letters = self.game.green_letters + green_letters
        self.game.yellow_letters = self.game.yellow_letters + yellow_letters
        self.game.black_letters = self.game.black_letters + black_letters

        wordle_image = create_full_wordle_pic(
            word=answer,
            lang=self.game.word_language,
            lives_count=self.game.lives_count,
            game_id=self.game.game_id,
            blocks=letter_blocks,
            green_letters=self.game.green_letters,
            yellow_letters=self.game.yellow_letters,
            black_letters=self.game.black_letters,
            prev_pic=self.game.image,
        )
        embed = get_embed(
            title=self.game.embed.title,
            description=self.game.embed.description,
            url_image=f"attachment://Usagi_wordle_game_{self.game.game_id}_{self.game.lives_count}.png"
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
                game_author_id=self.game.owner_id,
                lives_count=self.game.lives_count,
                game_id=self.game.game_id,
            )
        elif self.game.lives_count == 0:
            # lose condition
            await end_game(
                interaction=interaction,
                result="lose",
                word=self.game.word,
                game_author_id=self.game.owner_id,
                game_id=self.game.game_id,
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
            # owner answered
            await interaction.response.send_message("You guessed a word, you can't guess!", ephemeral=True)
            return
        await interaction.response.send_modal(WordleAnswer(game=self, title="Your answer!"))


async def generate_new_wordle_game(
        ctx: discord.ApplicationContext,
        word: str,
        game_type: str) -> None:
    """
    Create new game with params
    :param ctx: Application Context
    :param word: Word for game
    :param game_type: manual or auto game
    :return:
    """
    game_by = "by" if game_type == "manual" else "for"
    owner_id = ctx.author.id if game_type == "manual" else int(BOT_ID)

    first_letter = ord(word[0].upper())
    word_language = "russian"
    if 65 <= first_letter <= 90:
        word_language = "english"

    lives_count = len(word) + 1
    last_obj = await UsagiWordleGames.get_last_obj()
    if last_obj:
        last_id = last_obj.id + 1
    else:
        last_id = 1

    description = (
        f'''<a:sparkles:934435764564013076><a:sparkles:934435764564013076>
**Game #{last_id}** created {game_by} <@{ctx.author.id}>.
```ansi
[2;30m[0m[0;2mThe word contains — [0;36m{len(word)}[0m letters.
In {word_language} language.
You have only [0;36m{lives_count}[0m tries and it's time to spend it![0m
```
<a:sparkles:934435764564013076><a:sparkles:934435764564013076>'''
    )

    wordle_image = create_full_wordle_pic(
        word=word,
        lang=word_language,
        lives_count=lives_count,
        game_id=last_id,
    )
    embed = get_embed(
        title="New Wordle game!",
        description=description,
        url_image=f"attachment://Usagi_wordle_game_{last_id}_{lives_count}.png"
    )

    thread_name = f"Wordle Game #{last_id}"
    thread_type = discord.ChannelType.public_thread
    thread = await ctx.channel.create_thread(
        name=thread_name,
        type=thread_type,
        auto_archive_duration=1 * 60 * 24 * 3
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
            )
        )
        await message.pin(reason="Pin new game")
    except discord.ApplicationCommandInvokeError as e:
        ctx.bot.logger.INFO(e)

    await ctx.respond(f"Your game was created -> {thread.mention}", ephemeral=True)

    await UsagiWordleGames.create(
        guild_id=ctx.guild.id,
        word=word,
        owner_id=owner_id,
        thread_id=thread.id,
    )


def get_word(length: int) -> str | None:
    """
    Return random word from dict with specified length
    :param length: Length of word
    :return: New word
    """
    with open("./usagiBot/files/dicts/russian.txt", 'r', encoding="utf8") as f:
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
    with open("./usagiBot/files/dicts/check_dict.txt", "r", encoding="utf8") as f:
        words = f.readline().split(",")
    with open("./usagiBot/files/dicts/russian.txt", "r", encoding="utf8") as f:
        words2 = f.readline().split(",")
    return word_upper in words or word_upper in words2


def create_pic_for_answer(word: str, blocks: list[str]) -> Editor:
    """
    Generate colored image for input word
    :param word: Word
    :param blocks: Colors for word
    :return: New word image
    """
    green_block = Image.open("./usagiBot/files/photo/wordle/green_block.png").resize((153, 153))
    yellow_block = Image.open("./usagiBot/files/photo/wordle/yellow_block.png").resize((153, 153))
    black_block = Image.open("./usagiBot/files/photo/wordle/black_block.png").resize((153, 153))
    color_blocks = {
        "green_block": green_block,
        "yellow_block": yellow_block,
        "black_block": black_block,
    }
    background = Editor(Image.new("RGBA", (173 * len(blocks), 153), (255, 255, 255, 0)))
    font = ImageFont.truetype(font="./usagiBot/files/fonts/genshin.ttf", size=120)

    for i in range(len(blocks)):
        background.paste(color_blocks[blocks[i]], (173 * i, 0))
        if word[i] in "ЙЁ":
            background.text((173 * i + 30, 15), word[i], font=font, color="#fff")
        elif word[i] in "ШЖЩ":
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
                    position=(113 * place_counter + shift * layer_counter_place[layer_counter], 118 * layer_counter)
                )
            up = 30
            left = 25
            if letter in "ЙЁ":
                up = 15
            if letter in "ШЖЩ":
                left = 20
            blank.text(
                position=(
                    113 * place_counter + left + shift * layer_counter_place[layer_counter], 118 * layer_counter + up
                ),
                text=letter,
                font=font,
                color=color
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
    blank_block = Image.open("./usagiBot/files/photo/wordle/blank_block.png").resize((153, 153))
    background = Editor(Image.new("RGBA", (173 * length + 1600, 173 * (length + 1)), (255, 255, 255, 0)))
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
    keyboard_pic = create_pic_for_keyboard(green_letters, yellow_letters, black_letters, lang)
    if prev_pic is None:
        background = create_blank_words(length)
    else:
        prev_img = Image.open(prev_pic.fp)
        background = Editor(prev_img.resize((173 * length + 1600, 173 * (length + 1))))

    background.paste(word_pic, (0, 173 * word_x_pos))
    background.paste(keyboard_pic, (173 * length + 50, 86 * length))

    file = File(fp=background.image_bytes, filename=f"Usagi_wordle_game_{game_id}_{lives_count}.png")
    return file


async def create_finish_game_embed(
        interaction: discord.Interaction,
        result: str,
        word: str,
        game_author_id: int,
        game_id: int,
) -> discord.Embed:
    """
    Generate embed with finish info for wordle game
    :param game_id:
    :param interaction: Interaction
    :param result: result of game
    :param word: Guessed word
    :param game_author_id: Game creator id
    :return: Embed with finished game
    """
    game_author = await interaction.guild.fetch_member(game_author_id)
    if result == "win":
        winner = interaction.user.name
        discriminator = interaction.user.discriminator
    else:
        winner = "No one"
        discriminator = ""
    embed = get_embed(
        title=f"Wordle Game #{game_id} finished.",
        description=f'''```ansi
[0;2m[0m[0;2mWinner — {winner}#{discriminator}[0m[2;32m[0m
[0;2mWord — [0;32m[0;34m[0;36m[0;34m[0;32m[0;35m{word.upper()}[0m[0;32m[0m[0;34m[0m[0;36m[0m[0;34m[0m[0;32m[0m
Created by {game_author.name}#{game_author.discriminator}[0m[2;32m[4;32m[4;32m[0;32m[0m[4;32m[0m[4;32m[0m[2;32m[0m
```''',
    )
    return embed


async def end_game(
        interaction: discord.Interaction,
        result: str,
        word: str,
        game_author_id: int,
        game_id: int,
        lives_count: int = 0,
) -> None:
    """
    Last step when game finished, update data and notify winner.
    :param game_id:
    :param interaction: Interaction
    :param result: result of game
    :param word: Guessed word
    :param game_author_id: Game creator id
    :param lives_count: How many lives left
    :return:
    """
    wordle_channel = interaction.channel.parent
    finish_game_embed = await create_finish_game_embed(interaction, result, word, game_author_id, game_id)

    wordle_gamer = await UsagiWordleResults.get(guild_id=interaction.guild.id, user_id=interaction.user.id)
    if wordle_gamer:
        await UsagiWordleResults.update(
            id=wordle_gamer.id,
            points=wordle_gamer.points + lives_count,
            count_of_games=wordle_gamer.count_of_games + 1,
        )
    else:
        await UsagiWordleResults.create(
            guild_id=interaction.guild.id,
            user_id=interaction.user.id,
            points=lives_count,
            count_of_games=1
        )

    await wordle_channel.send(embed=finish_game_embed)
    await interaction.channel.edit(archived=True, locked=True)
