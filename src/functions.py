import discord
from datetime import datetime
import pytz


def createEmbed(title = None, description = None, color = 0x00ff00, urlImage = None, thumbnail = None, footer = None, authorName = None, authorIconURL = None):
    embed = discord.Embed(title = title, description = description, color = color)
    if urlImage:
        embed.set_image(url = urlImage)

    if thumbnail:
        embed.set_thumbnail(url = thumbnail)

    if footer:
        embed.set_footer(text = footer)

    if authorName:
        embed.set_author(name = authorName, icon_url = authorIconURL)

    return embed


def isCommand(msg, cmdList):
    for cmd in cmdList:
        if len(msg.split(cmd)) >= 2: return 1

    return 0

def getCurrentTime():
    IST = pytz.timezone('Europe/Moscow')
    return datetime.now(IST).strftime("%H:%M")


async def wrongMessage(data, title = None, description = None, delay = 10):
    embed = createEmbed(title = title, description = description)
    await data['message'].channel.send('<@{0}>'.format(data['message'].author.id), embed = embed, delete_after = delay)


def newLog(text, new = None):
    if new:
        file = open('logs.txt', 'w')
        file.write('Logs\n')
    else:
        file = open('logs.txt', 'w')
    file.write('\n' + text)
    file.close()
