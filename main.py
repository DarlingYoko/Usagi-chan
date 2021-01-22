import config
import discord
from src.functions import *
import shelve
from discord.utils import get

client = discord.Client()
LOGGER = config.getLogger()

valentineCommandAnon = '!валентика'
valentineCommandDeAnon = '!девалентика'
simpleMesageCommand = '!m'
voiceCommand = '!connect'



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

    #LOGGER.info(message)

    urlImage = ''
    logChannel = client.get_channel(config.logChannel)
    messageChannel = client.get_channel(config.messageChannel)
    userName = message.author.display_name


    #only private messages
    try:
        UID = message.channel.recipient.id

        #check attachments
        if message.attachments:
            if len(message.attachments) > 1:
                await message.channel.send('Слишком много дополнительных файлов.\nВы можете прикрепить только одну картинку.')
                return
            else:
                urlImage = message.attachments[0].url

        if message.content.startswith(valentineCommandAnon):
            embedLog = createEmbed(title = "Новая заявка",
                                   description = 'Пользователь - <@{0}>\nСообщение - {1}\n'.format(UID, message.content.split(valentineCommandAnon)[1]),
                                   color = 0x00ff00,
                                   urlImage = urlImage)

            embedMes = createEmbed(title = "Анонимная валентинка!",
                                   description = '{0}\n'.format(message.content.split(valentineCommandAnon)[1]),
                                   color = 0x00ff00,
                                   urlImage = urlImage,
                                   thumbnail = config.thumbnail)

            await logChannel.send(embed=embedLog)
            await messageChannel.send(embed=embedMes)
            await message.channel.send('Анонимная валентинка успешно отправлена!')

        if message.content.startswith(valentineCommandDeAnon):
            embedLog = createEmbed(title = "Новая заявка",
                                   description = '**Пользователь** - <@{0}>\n**Сообщение** - {1}\n'.format(UID, message.content.split(valentineCommandDeAnon)[1]),
                                   color = 0x00ff00,
                                   urlImage = urlImage)

            embedMes = createEmbed(title = "Валентинка от {0}!".format(userName),
                                   description = '{1}\n'.format(UID, message.content.split(valentineCommandDeAnon)[1]),
                                   color = 0x00ff00,
                                   urlImage = urlImage,
                                   thumbnail = config.thumbnail)

            await logChannel.send(embed=embedLog)
            await messageChannel.send(embed=embedMes)
            await message.channel.send('Неанонимная валентинка успешно отправлена!')

        if message.content.startswith(simpleMesageCommand):
            logChannel = client.get_channel(346775939709009920)
            await logChannel.send(message.content.split(simpleMesageCommand)[1])


    except AttributeError:
        pass

    except Exception as e:
        LOGGER.exception('Exception: ' + str(e))

@client.event
async def on_voice_state_update(member, before, after):
    if member.id == config.yokoId:
        if before.channel and after.channel:
            channel = discord.utils.get(client.voice_clients, channel=before.channel)
            await channel.disconnect()
            channel = client.get_channel(after.channel.id)
            await channel.connect()

        elif before.channel:
            channel = discord.utils.get(client.voice_clients, channel=before.channel)
            await channel.disconnect()

        else:
            channel = client.get_channel(after.channel.id)
            await channel.connect()
    else:
        return


client.run(config.token)

#346775939709009920
#member = await guild.fetch_member(UID)
