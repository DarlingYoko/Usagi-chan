import discord
import logging
import os
import json
from discord.ext import commands
from pycord18n.extension import I18nExtension, Language

from usagiBot.env import COGS_DIR
from usagiBot.src.CustomHelpCommand import CustomHelpCommand

# Define bot
intents = discord.Intents.all()
bot = commands.Bot(
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
for cog_name in os.listdir(COGS_DIR):
    if "index.py" in os.listdir(f"./{COGS_DIR}/{cog_name}"):
        cogs_dir_with_dots = COGS_DIR.replace("/", ".")
        bot.load_extension(f"{cogs_dir_with_dots}.{cog_name}.index")

# Define language
i18n = I18nExtension([
    Language("English", "en", json.load(open("usagiBot/files/language/en.json"))),
    Language("Russian", "ru", json.load(open("usagiBot/files/language/ru.json"))),
], fallback="en")


def get_locale(ctx):
    return ctx.bot.language.get(ctx.author.id, "en")


i18n.init_bot(bot, get_locale)
bot.i18n = i18n
