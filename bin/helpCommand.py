import discord
from discord.ext import commands
from discord_components import DiscordComponents
from bin.functions import *
import itertools

class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping):
        ctx = self.context
        #components = get_query_btns(ctx, f'Page 0/0')
        title = 'Usagi commands'
        description = 'Happy enjoy! ／(◕ω ◕)＼♡°'
        url_image = 'https://cdn.discordapp.com/attachments/690999933356081193/691029773392019506/divider.gif'
        #thumbnail = 'https://cdn.discordapp.com/attachments/813825744789569537/881690163120599050/iconUSAGI.png'
        fields = []
        counter = itertools.count()
        next(counter)
        for cog in mapping:
            if cog and cog.get_commands():
                name = f'｢{cog.qualified_name} ｣'
                value_commands = {}
                for command in cog.get_commands():
                    if command.help:
                        if command.help in value_commands.keys():
                            value_commands[command.help] += f' !{command.name}'
                        else:
                            value_commands[command.help] = f'!{command.name}'
                        #value += f'`!{command.name}`\n╰➣[<#{command.help}>](https://ptb.discord.com/channels/733631069542416384/{command.help}/)\n'
                    else:
                        if '#All_channels' in value_commands.keys():
                            value_commands['#All_channels'] += f' !{command.name}'
                        else:
                            value_commands['#All_channels'] = f'!{command.name}'

                        #value += f'`!{command.name}`\n╰➣#All_channels\n'
                value = ''
                for key, item in value_commands.items():
                    if key != '#All_channels':
                        value += f'`{item}`\n╰➣[<#{key}>](https://ptb.discord.com/channels/733631069542416384/{key}/)\n'
                    else:
                        value += f'`{item}`\n╰➣#All_channels\n'

                if next(counter) %2 == 0:
                    fields.append({'name': '_ _', 'value': '_ _', 'inline': True})
                fields.append({'name': name, 'value': value, 'inline': True})

        embed = get_embed(title = title, description = description, fields = fields, url_image = url_image)
        await ctx.send(embed = embed)#, components = components)



    async def send_cog_help(self, cog):
        ctx = self.context
        #components = get_query_btns(ctx, f'Page 0/0')
        title = f'｢{cog.qualified_name} ｣'
        url_image = 'https://cdn.discordapp.com/attachments/690999933356081193/691029773392019506/divider.gif'
        thumbnail = 'https://cdn.discordapp.com/attachments/813825744789569537/881690163120599050/iconUSAGI.png'

        value_commands = {}
        for command in cog.get_commands():
            if command.help:
                if command.help in value_commands.keys():
                    value_commands[command.help] += f' !{command.name}'
                else:
                    value_commands[command.help] = f'!{command.name}'
            else:
                if '#All_channels' in value_commands.keys():
                    value_commands['#All_channels'] += f' !{command.name}'
                else:
                    value_commands['#All_channels'] = f'!{command.name}'

        description = ''
        for key, item in value_commands.items():
            if key != '#All_channels':
                description += f'`{item}`\n╰➣[<#{key}>](https://ptb.discord.com/channels/733631069542416384/{key}/)\n'
            else:
                description += f'`{item}`\n╰➣#All_channels\n'


        embed = get_embed(title=title, description=description, url_image=url_image, thumbnail=thumbnail)
        await ctx.send(embed = embed)#, components = components)
        #await self.get_destination().send(f'{cog.qualified_name}: {[command.name for command in cog.get_commands()]}')

    async def send_group_help(self, group):
        ctx = self.context

        desc = f'{group.description}\n' if group.description else '_ _\n'

        commands = '\n\t!'.join([f'{get_parents(command)} {command.name} {command.brief if command.brief else ""}' for index, command in enumerate(group.commands)])
        key = f'[<#{group.help}>](https://ptb.discord.com/channels/733631069542416384/{group.help}/)' if group.help else '#All_channels'
        description = f'{desc}\n```ARM\nCommands\n\t!{commands}```╰➣{key}'

        url_image = 'https://cdn.discordapp.com/attachments/690999933356081193/691029773392019506/divider.gif'
        thumbnail = 'https://cdn.discordapp.com/attachments/813825744789569537/881690163120599050/iconUSAGI.png'
        embed = get_embed(title = f'｢{group.name} ｣', description = description, url_image = url_image, thumbnail = thumbnail)
        await ctx.send(embed = embed)
        #await self.get_destination().send(f'{group.name}: {[command.name for indexm, command in enumerate(group.commands)]}')

    async def send_command_help(self, command):
        ctx = self.context

        desc = f'{command.description}\n' if command.description else '_ _\n'
        if command.aliases:
            aliases = f'[{command.qualified_name}|' + '|'.join(command.aliases) + ']'
        else:
            aliases = f'[{command.qualified_name}]'
        usage = f'  {command.usage}' if command.usage else ''

        key = f'[<#{command.help}>](https://ptb.discord.com/channels/733631069542416384/{command.help}/)' if command.help else '#All_channels'
        description = f'{desc}\n```!{aliases}{usage}```╰➣{key}'

        url_image = 'https://cdn.discordapp.com/attachments/690999933356081193/691029773392019506/divider.gif'
        thumbnail = 'https://cdn.discordapp.com/attachments/813825744789569537/881690163120599050/iconUSAGI.png'
        embed = get_embed(title = f'｢{command.name} ｣', description = description, url_image = url_image, thumbnail = thumbnail)
        await ctx.send(embed = embed)
        #await self.get_destination().send(command.name)


def get_parents(command):
    if command.parents:
        parents = command.parents.copy()
        parents.reverse()
        return ' '.join([i.name for i in parents])
    else:
        return ''
