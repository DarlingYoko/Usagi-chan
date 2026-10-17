import os

BOT_TOKEN = os.environ.get("DISCORD_TOKEN")
BOT_OWNER = int(os.environ.get("BOT_OWNER"))
BOT_ID = int(os.environ.get("BOT_ID"))

COGS_DIR = os.environ.get("COGS_DIR")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

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

VPN_USERNAME = os.environ.get("VPN_USERNAME")
VPN_PASSWORD = os.environ.get("VPN_PASSWORD")
VPN_API_URL = os.environ.get("VPN_API_URL")
VPN_SUB_URL = os.environ.get("VPN_SUB_URL")

SHARED_FOLDER_URL = os.environ.get("SHARED_FOLDER_URL")
