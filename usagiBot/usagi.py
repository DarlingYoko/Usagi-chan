import discord, os, logging
from discord.ext import commands
from usagiBot.env import COGS_DIR
from usagiBot.src.CustomHelpCommand import CustomHelpCommand


# Define bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix="?",
    intents=intents,
    help_command=CustomHelpCommand(),
    debug_guilds=[733631069542416384, 955858929496231976],
)

# Define logger
bot.logger = logging.getLogger("mylogger")
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# Define variables
bot.command_tags = []
bot.wordle_games = {}

# Define cogs
for cog_name in os.listdir(COGS_DIR):
    if "index.py" in os.listdir(f"./{COGS_DIR}/{cog_name}"):
        cogs_dir_with_dots = COGS_DIR.replace("/", ".")
        bot.load_extension(f"{cogs_dir_with_dots}.{cog_name}.index")
