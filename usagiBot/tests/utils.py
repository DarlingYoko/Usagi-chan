from pycord18n.extension import I18nExtension, Language
import json
import os

os.environ["BOT_OWNER"] = "11111"
os.environ["BOT_ID"] = "1234567890"


def init_i18n():
    i18n = I18nExtension([
        Language("English", "en", json.load(open("usagiBot/files/language/en.json", encoding='utf-8'))),
        Language("Russian", "ru", json.load(open("usagiBot/files/language/ru.json", encoding='utf-8'))),
    ], fallback="en")

    return i18n


def get_locale(ctx):
    return "en"
