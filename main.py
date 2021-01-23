import discord
import src.config as config
from src.functions import *
from src.privateCommands import *
from discord.utils import get
from src.config import privateCommands


client = discord.Client()
LOGGER = config.getLogger()


guildCommands = []



@client.event
async def on_ready():
    LOGGER.info('Successfully connected')

    '''
    channel = client.get_channel(791757047800659969)
    message = await channel.fetch_message(793189861065490452)
    embeds = message.embeds
    for embed in embeds:
        print(embed.to_dict())
        print()
    '''

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    #LOGGER.info(message.channel)

    urlImage = None
    userName = message.author.display_name
    UID = message.author.id
    msg = message.content

    if message.attachments:
        urlImage = message.attachments[0].url

    #private messages
    if isCommand(msg, privateCommands.values()):
        if str(message.channel.type) == 'private':

            splitStr = privateCommands['valentineCommandAnon']
            if msg.startswith(splitStr):
                await valentineCommand(client = client,
                                       message = message,
                                       UID = UID,
                                       splitStr = splitStr,
                                       urlImage = urlImage)


            splitStr = privateCommands['valentineCommandDeAnon']
            if msg.startswith(splitStr):
                await valentineCommand(client = client,
                                       message = message,
                                       UID = UID,
                                       splitStr = splitStr,
                                       urlImage = urlImage,
                                       anon = False)

            splitStr = privateCommands['deleteValentine']
            if msg.startswith(splitStr):
                await deleteValentine(client = client,
                                      message = message,
                                      UID = UID,
                                      splitStr = splitStr)

            if msg.startswith(privateCommands['simpleMesageCommand']):
                logChannel = client.get_channel(346775939709009920)
                logChannel.send(msg.split(simpleMesageCommand)[1])

        # channel messages
        else:
            timeMsg = await message.channel.send('<@{0}>, эта команда только для личных сообщений'.format(UID))
            await message.delete()
            await timeMsg.delete(delay = 3)

        return

    elif isCommand(msg, guildCommands):
        return


@client.event
async def on_voice_state_update(member, before, after):
    if member.id == config.yokoId:

        if before.channel and after.channel and before.channel.id != after.channel.id:
            channel = discord.utils.get(client.voice_clients, channel=before.channel)
            await channel.disconnect()
            channel = client.get_channel(after.channel.id)
            await channel.connect()

        elif before.channel and before.self_mute == after.self_mute and before.self_deaf == after.self_deaf:
            channel = discord.utils.get(client.voice_clients, channel=before.channel)
            await channel.disconnect()

        elif after.channel and before.self_mute == after.self_mute and before.self_deaf == after.self_deaf:
            channel = client.get_channel(after.channel.id)
            await channel.connect()
    else:
        return


client.run(config.token)

#346775939709009920
#member = await guild.fetch_member(UID)
