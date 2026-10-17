from cryptography.fernet import Fernet
from pycord18n.extension import I18nExtension, Language
import json
import os

os.environ["BOT_OWNER"] = "11111"
os.environ["BOT_ID"] = "1234567890"
os.environ.setdefault(
    "CREDENTIALS_ENCRYPTION_KEY", Fernet.generate_key().decode()
)
# Engine creation is lazy (no connection at import), but the URL must
# parse — unset vars stringify to "None" and crash on int("None") port
# whenever db.base gets imported outside a create_async_engine patch.
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")


def init_i18n():
    i18n = I18nExtension(
        [
            Language(
                "English",
                "en",
                json.load(open("usagiBot/files/language/en.json", encoding="utf-8")),
            ),
            Language(
                "Russian",
                "ru",
                json.load(open("usagiBot/files/language/ru.json", encoding="utf-8")),
            ),
        ],
        fallback="en",
    )

    return i18n


def get_locale(ctx):
    return "en"
