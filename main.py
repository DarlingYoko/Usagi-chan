import discord
import os, sys, traceback
from discord.ext import commands
from bin.functions import get_config
from discord_components import DiscordComponents
from importlib import reload as reload_module
from bin.helpCommand import CustomHelpCommand


intents = discord.Intents().all()
bot = commands.Bot(command_prefix = '!', intents = intents, help_command = CustomHelpCommand())

config = get_config()

for dir in os.listdir('./cogs'):
    if 'index.py' in os.listdir(f'./cogs/{dir}'):
        bot.load_extension(f'cogs.{dir}.index')



token = config['data'].get('token')

@bot.event
async def on_ready():
    print('Bot is up')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("!help | ver 3.0 | Beta-test |"))
    DiscordComponents(bot)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Такой команды не существует.')
    else:
        print(error)



@bot.command()
@commands.is_owner()
async def load(ctx, arg: str):
    bot.load_extension(f'cogs.{arg}.index')
    await ctx.send('Успешно подключила ког.')

@bot.command()
@commands.is_owner()
async def unload(ctx, arg: str):
    bot.unload_extension(f'cogs.{arg}.index')
    await ctx.send('Успешно отключила ког.')

@bot.command()
@commands.is_owner()
async def reload(ctx, arg: str):
    modules = list(sys.modules.values()).copy()
    try:
        for module in modules:
            if f'cogs.{arg}' in module.__name__:
                reload_module(module)
                print(module.__name__)
    except Exception as e:
        print(traceback.format_exc())

    bot.reload_extension(f'cogs.{arg}.index')
    await ctx.send('Успешно перезагрузила ког.')



bot.run(token)


#обновить все пакеты
