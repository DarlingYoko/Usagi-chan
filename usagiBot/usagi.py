import discord, os, platform, logging
from discord.ext import commands
from usagiBot.env import COGS_DIR
from usagiBot.src.UsagiUtils import error_notification_to_owner, load_all_command_tags
from usagiBot.src.CustomHelpCommand import CustomHelpCommand
from usagiBot.src.UsagiErrors import UsagiNotSetUpError

# Define bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix="?",
    intents=intents,
    help_command=CustomHelpCommand(),
    debug_guilds=[733631069542416384, 955858929496231976],
)

bot.command_tags = []

# Define logger
logger = logging.getLogger("mylogger")
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# Define cogs
for cog_name in os.listdir(COGS_DIR):
    if "index.py" in os.listdir(f"./{COGS_DIR}/{cog_name}"):
        cogs_dir_with_dots = COGS_DIR.replace("/", ".")
        bot.load_extension(f"{cogs_dir_with_dots}.{cog_name}.index")


# Define main events
@bot.event
async def on_ready():
    await load_all_command_tags(bot)
    logger.info("---------NEW SESSION----------")
    logger.info(f"Logged in as {bot.user.name}")
    logger.info(f"discord.py API version: {discord.__version__}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    logger.info(f"Loaded command tags: {bot.command_tags}")
    logger.info(f"Connected to database ")
    logger.info("-------------------")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply("Такой команды не существует.", delete_after=2 * 60)
    elif isinstance(error, commands.CommandOnCooldown):
        retry_after = float(error.retry_after)
        await ctx.reply(
            f"Эту команду ты сможешь использовать через {retry_after:.0f}s",
            delete_after=2 * 60,
        )
    elif isinstance(error, UsagiNotSetUpError):
        await ctx.reply(
            "This command was not configured. Contact the server administration.",
            delete_after=2 * 60,
        )
    elif isinstance(error, discord.errors.CheckFailure):
        await ctx.respond("Some requirements were not met.", delete_after=2 * 60)
    else:
        await error_notification_to_owner(ctx, error)


@bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, discord.errors.CheckFailure):
        await ctx.respond("Some requirements were not met.", ephemeral=True)
    elif isinstance(error, UsagiNotSetUpError):
        await ctx.respond(
            "This command was not configured. Contact the server administration.",
            ephemeral=True,
        )
    elif isinstance(error, commands.CommandOnCooldown):
        retry_after = float(error.retry_after)
        await ctx.respond(
            f"Эту команду ты сможешь использовать через {retry_after:.0f}s",
            ephemeral=True,
        )
    else:
        await error_notification_to_owner(ctx, error, app_command=True)
