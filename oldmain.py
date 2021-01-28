import discord, asyncio
import src.config as config
from src.functions import *
from src.privateCommands import *
from src.guildCommands import *
from discord.utils import get
from src.config import privateCommands, guildCommands
from src.classMember import Members
from threading import Thread



intents = discord.Intents.all()
client = discord.Client(intents=intents)
LOGGER = config.getLogger()
members = Members(config.guildId)



@client.event
async def on_ready():
    LOGGER.info('Successfully connected')
    members.setClient(client)
    await members.fillMembers()



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
    return
    if str(message.type) == 'MessageType.pins_add':
        await message.delete()
        return

    if message.author == client.user:
        return
    if message.guild.id == 346775939105161247:
        return

    #msg = await message.channel.fetch_message(802967352052154398)  # Can be None if msg was deleted
    #react = msg.reactions[0]
    #users = await react.users().flatten()
    #print(users)

    #await message.channel.send(embed = createEmbed(description = str(message.author.avatar_url_as())[:-10]))

    #print(message.type)


    msg = message.content
    data = {'client': client,
            'ID': message.author.id,
            'attachmentURL': None,
            'message': message}


    if message.attachments:
        data['urlImage'] = message.attachments[0].url

    #private messages
    if isCommand(msg, privateCommands.values()):
        if str(message.channel.type) == 'private':

            splitStr = privateCommands['createValentine']
            if msg.startswith(splitStr):
                data['content'] = msg.split(splitStr)[1]
                await valentineCommand(data = data, members = members)

            splitStr = privateCommands['deleteValentine']
            if msg.startswith(splitStr):
                data['content'] = msg.split(splitStr)[1]
                await deleteValentine(data = data)

            if msg.startswith(privateCommands['simpleMessageCommand']):
                if UID == config.yokoId:
                    logChannel = client.get_channel(346775939709009920)
                    logChannel.send(msg.split(simpleMessageCommand)[1])
                else:
                    await message.channel.send('Ты не мой создатель!')

        # channel messages
        else:
            timeMsg = await message.channel.send('<@{0}>, эта команда только для личных сообщений'.format(UID))
            await message.delete()
            await timeMsg.delete(delay = 3)
            #pass
        return

    elif isCommand(msg, guildCommands.values()):
        if str(message.channel.type) == 'text':
            splitStr = guildCommands['createRequest']
            if msg.startswith(splitStr):
                data['content'] = msg.split(splitStr)[1]
                await createRequest(data = data)
                #timeMsg = await message.channel.send('Сообщение с эмоутом')
                #await timeMsg.add_reaction('<:Sugimoto:797242409757966346>')

            splitStr = guildCommands['helpCommand']
            if msg.startswith(splitStr):
                await helpCommand(data = data)


        else:
            timeMsg = await message.channel.send('<@{0}>, эта команда только для каналов'.format(UID))
            await timeMsg.delete(delay = 3)

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

@client.event
async def on_member_join(member):
    #LOGGER.info('MEMBER JOIN')
    #members.addMember(member)
    pass

@client.event
async def on_member_remove(member):
    #LOGGER.info('MEMBER LEAVE')
    #members.removeMember(member)
    pass

@client.event
async def on_user_update(before, after):
    #if before.name != after.name:
        #members.updateName(after.name, after.id)

    #if before.discriminator != after.discriminator:
        #members.updateTag(after.discriminator, after.id)
    pass

@client.event
async def on_raw_reaction_add(payload):
    return
    if payload.guild_id == 346775939105161247:
        return
    await fillEmoji(payload, client)

@client.event
async def on_raw_reaction_remove(payload):
    return
    if payload.guild_id == 346775939105161247:
        return
    await dellEmoji(payload, client)


async def checkRequests():
    while True:
        #check requests for over time
        await asyncio.sleep(5 * 60)


Thread(target=client.run, args=(config.token, )).start()
asyncio.run(checkRequests())


#346775939709009920
#member = await guild.fetch_member(UID)
#!создать 7/704954930/3/Чурликов быстренько, а то завтра на работу
