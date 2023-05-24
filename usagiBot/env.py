import os

BOT_TOKEN = os.environ.get("DISCORD_TOKEN")
TEST_BOT_TOKEN = os.environ.get("DISCORD_TEST_TOKEN")
DISCORD_TEST2_TOKEN = os.environ.get("DISCORD_TEST2_TOKEN")
BOT_OWNER = int(os.environ.get("BOT_OWNER"))
BOT_ID = int(os.environ.get("BOT_ID"))

COGS_DIR = os.environ.get("COGS_DIR")

DATABASE_NAME = os.environ.get("DATABASE_NAME")
DATABASE_USER = os.environ.get("DATABASE_USER")
DATABASE_PASS = os.environ.get("DATABASE_PASS")
DATABASE_HOST = os.environ.get("DATABASE_HOST")
DATABASE_PORT = os.environ.get("DATABASE_PORT")

TWITCH_TOKEN = os.environ.get("TWITCH_TOKEN")
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")