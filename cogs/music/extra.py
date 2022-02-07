import discord
import itertools
from discord.ext import commands
from youtube_dl import YoutubeDL
from discord.ui import Button, Select
from discord import ButtonStyle, SelectOption


def get_search_btns(ctx):
    emojiOne = ctx.bot.get_emoji(877562925253001297)
    emojiTwo = ctx.bot.get_emoji(877562925752139846)
    emojiThree = ctx.bot.get_emoji(877562925525639169)
    emojiFour = ctx.bot.get_emoji(877562925563408434)
    emojiFive = ctx.bot.get_emoji(877562925181714463)

    btn1 = Button(style=ButtonStyle.gray, emoji = emojiOne, id = '0')
    btn2 = Button(style=ButtonStyle.gray, emoji = emojiTwo, id = '1')
    btn3 = Button(style=ButtonStyle.gray, emoji = emojiThree, id = '2')
    btn4 = Button(style=ButtonStyle.gray, emoji = emojiFour, id = '3')
    btn5 = Button(style=ButtonStyle.gray, emoji = emojiFive, id = '4')
    components=[[btn1, btn2, btn3, btn4, btn5,]]

    return components



def get_info_by_URL(URL):
    print(URL)
    ydl_opts = {
        'ignoreerrors': True,
        'audio-format': 'mp3',
        'yes-playlist': True,
        'verbose': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(URL, download=False)

    return info


def add_track(self, info, user_name):
    if info:
        track = f'Track {next(self.counter)}'
        id = info['id']
        self.queryList.append(track)
        self.queryData[track] = {
            'title': info['title'],
            'URL': f'https://www.youtube.com/watch?v={id}',
            'duration': info['duration'],
            'user': user_name,}


def get_sec(time_str):
    time = [int(i) for i in time_str.split(':')]
    start = 1
    result = 0
    for per in time[::-1]:
        result += (per * start)
        start *= 60
    return result
