import discord
import logging
import os
import json
from discord.ext import commands
from pycord18n.extension import I18nExtension, Language

from usagiBot.db.models import create_tables
from usagiBot.env import COGS_DIR
from usagiBot.src.CustomHelpCommand import CustomHelpCommand


class UsagiBot(commands.Bot):
    async def before_identify_hook(self, shard_id, *, initial=False):
        self.logger.info("Running DB migrations before bot connect")
        await create_tables()
        self.logger.info("DB Ready")

# Define bot
intents = discord.Intents.all()
bot = UsagiBot(
    command_prefix="!",
    intents=intents,
    help_command=CustomHelpCommand(),
)

# Define logger
bot.logger = logging.getLogger("mylogger")
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# Define variables
bot.command_tags = []
bot.wordle_games = {}
bot.language = {}
bot.ai_questions = {}

# Define cogs
bot.logger.info("---------LOADING COGS----------")
for cog_name in os.listdir(COGS_DIR):
    if "index.py" in os.listdir(f"./{COGS_DIR}/{cog_name}"):
        bot.logger.info(f"Loading cog: {cog_name}")
        cogs_dir_with_dots = COGS_DIR.replace("/", ".")
        bot.load_extension(f"{cogs_dir_with_dots}.{cog_name}.index")
bot.logger.info("---------ALL COGS LOADED-------")

# Define language
i18n = I18nExtension(
    [
        Language("English", "en", json.load(open("usagiBot/files/language/en.json"))),
        Language("Russian", "ru", json.load(open("usagiBot/files/language/ru.json"))),
    ],
    fallback="en",
)


def get_locale(ctx):
    return ctx.bot.language.get(ctx.author.id, "en")


i18n.init_bot(bot, get_locale)
bot.i18n = i18n
