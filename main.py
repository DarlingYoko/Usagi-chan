import discord
import os
from discord.ext import commands
from bin.functions import *

async def isAdmin(ctx):
    return ctx.author.id == 824521926416269312







bot = commands.Bot(command_prefix = '!')

config = get_config()

for dir in os.listdir('./cogs'):
    if 'index.py' in os.listdir(f'./cogs/{dir}'):
        bot.load_extension(f'cogs.{dir}.index')



token = config['data'].get('token')

@bot.event
async def on_ready():
    print('Bot is up')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Такой команды не существует.')
    else:
        print(error)

@bot.command()
@commands.check(isAdmin)
async def load(ctx, arg):
    bot.load_extension(f'cogs.{arg}.index')
    await ctx.send('Успешно подключила ког.')

@bot.command()
@commands.check(isAdmin)
async def unload(ctx, arg):
    bot.unload_extension(f'cogs.{arg}.index')
    await ctx.send('Успешно отключила ког.')

@bot.command()
@commands.check(isAdmin)
async def reload(ctx, arg):
    bot.reload_extension(f'cogs.{arg}.index')
    await ctx.send('Успешно перезагрузила ког.')



bot.run(token)
