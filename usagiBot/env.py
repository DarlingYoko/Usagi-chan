import os

BOT_TOKEN = os.environ.get("DISCORD_TOKEN")
TEST_BOT_TOKEN = os.environ.get("DISCORD_TEST_TOKEN")
DISCORD_TEST2_TOKEN = os.environ.get("DISCORD_TEST2_TOKEN")
BOT_OWNER = int(os.environ.get("BOT_OWNER"))
BOT_ID = int(os.environ.get("BOT_ID"))

HOYOLAB_CLIENT_ID = os.environ.get("HOYOLAB_CLIENT_ID")
HOYOLAB_CLIENT_SECRET = os.environ.get("HOYOLAB_CLIENT_SECRET")

COGS_DIR = os.environ.get("COGS_DIR")

POSTGRES_DB = os.environ.get("POSTGRES_DB")
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT")

TWITCH_TOKEN = os.environ.get("TWITCH_TOKEN")
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
