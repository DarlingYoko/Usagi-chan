import discord
import logging
import os
import json
from discord.ext import commands
from pycord18n.extension import I18nExtension, Language

from usagiBot.db.models import create_tables
from usagiBot.env import COGS_DIR
from usagiBot.src.CustomHelpCommand import CustomHelpCommand
from usagiBot.src.UsagiUtils import init_language


class UsagiBot(commands.Bot):
    def __init__(self, command_prefix, help_command, intents):
        super().__init__(command_prefix, help_command, intents=intents)
        self.language = None

        # Define logger
        self.logger = logging.getLogger("mylogger")
        logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

        # Define variables
        self.command_tags = []
        self.wordle_games = {}
        self.ai_questions = {}

        # Define cogs
        self.logger.info("---------LOADING COGS----------")
        for cog_name in os.listdir(COGS_DIR):
            if "index.py" in os.listdir(f"./{COGS_DIR}/{cog_name}"):
                self.logger.info(f"Loading cog: {cog_name}")
                cogs_dir_with_dots = COGS_DIR.replace("/", ".")
                self.load_extension(f"{cogs_dir_with_dots}.{cog_name}.index")
        self.logger.info("---------ALL COGS LOADED-------")

        # Define language
        with open("usagiBot/files/language/en.json", encoding="utf-8") as en_file:
            en_dict = json.load(en_file)
        with open("usagiBot/files/language/ru.json", encoding="utf-8") as ru_file:
            ru_dict = json.load(ru_file)
        i18n = I18nExtension(
            [
                Language("English", "en", en_dict),
                Language("Russian", "ru", ru_dict),
            ],
            fallback="en",
        )

        def get_locale(ctx):
            return ctx.bot.language.get(ctx.author.id, "en")

        i18n.init_bot(self, get_locale)
        self.i18n = i18n

    async def before_identify_hook(self, shard_id, *, initial=False):
        # Fires before every (re)identify; one-time DB/lang setup belongs to
        # the first connect only, not to each reconnect.
        if not initial:
            return

        self.logger.info("Running DB migrations before bot connect")
        await create_tables()
        self.logger.info("DB Ready")

        self.logger.info("Loading Languages")
        self.language = await init_language()
        self.logger.info("Languages loaded")

# Define bot — only the gateway events the cogs actually consume;
# Intents.all() subscribed to presences/typing, the highest-volume events
usegi_intents = discord.Intents(
    guilds=True,
    members=True,
    messages=True,
    message_content=True,
    reactions=True,
    voice_states=True,
    emojis=True,
)
bot = UsagiBot(
    command_prefix="!",
    intents=usegi_intents,
    help_command=CustomHelpCommand(),
)
