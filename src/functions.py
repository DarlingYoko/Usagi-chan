import discord, pytz, logging.config, configparser
from datetime import datetime
import sys, os

def createEmbed(title = None, description = None, color = 0x00ff00, urlImage = None, thumbnail = None, footer = None, authorName = None, authorIconURL = None):
    embed = discord.Embed(description = description, color = color)
    if urlImage:
        embed.set_image(url = urlImage)

    if thumbnail:
        embed.set_thumbnail(url = thumbnail)

    if footer:
        embed.set_footer(text = footer)

    if authorName:
        embed.set_author(name = authorName, icon_url = authorIconURL)

    if title:
        embed.title = title


    return embed


def isCommand(msg, cmdList):
    for cmd in cmdList:
        if len(msg) > 0 and msg.split()[0].lower() == cmd: return 1

    return 0

def getCurrentTime():
    IST = pytz.timezone('Europe/Moscow')
    return datetime.now(IST).strftime("%H:%M")


async def wrongMessage(message, title = None, description = None, delay = 10):
    embed = createEmbed(title = title, description = description)
    await message.channel.send('<@{0}>'.format(message.author.id), embed = embed, delete_after = delay)


def newLog(exc_type, exc_obj, exc_tb, e, new = None):
    file = open('../../logs.txt', 'a')
    if new:
        file.write('\n\nLogs new start\n')
    else:
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        file.write('\n' + 'New error in creating request at {0}:\ntype - {1}, name - {2}, line - {3}, error - {4}\n'.format(datetime.now(), exc_type, fname, exc_tb.tb_lineno, e))
    file.close()


def loadConfig(name):
    config = configparser.ConfigParser()
    config.read('{0}.ini'.format(name), encoding = 'UTF8')
    return config


def getLogger():
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(name)s] %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "level": "INFO",
            "handlers": [
                "console"
            ]
        }
    })

    return logging.getLogger()
