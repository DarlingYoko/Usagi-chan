import config
import discord
from src.functions import *
import shelve

client = discord.Client()
LOGGER = config.getLogger()
valentineCommandAnon = '!new'
valentineCommandDeAnon = '!newde'
simpleMesageCommand = '!m'



@client.event
async def on_ready():
    LOGGER.info('Successfully connected')



@client.event
async def on_message(message):

    if message.author == client.user:
        return

    #LOGGER.info(message)

    channel = client.get_channel(733631069542416387)
    msg = await channel.fetch_message(801580586636279840)
    await msg.delete()

    urlImage = ''
    logChannel = client.get_channel(config.logChannel)
    messageChannel = client.get_channel(config.messageChannel)

    #check attachments
    if message.attachments:
        if len(message.attachments) > 1:
            await message.channel.send('Слишком много дополнительных файлов.\nВы можете прикрепить только одну картинку.')
            return
        else:
            urlImage = message.attachments[0].url

    #only private messages
    try:
        UID = message.channel.recipient.id
        if message.content.startswith(valentineCommandAnon):
            embedLog = createEmbed(title = "Новая заявка",
                                   description = 'Пользователь - <@{0}>\nСообщение - {1}\n'.format(UID, message.content.split(valentineCommandAnon)[1]),
                                   color = 0x00ff00,
                                   urlImage = urlImage)

            embedMes = createEmbed(title = "Новая валентика",
                                   description = '{0}\n'.format(message.content.split(valentineCommandAnon)[1]),
                                   color = 0x00ff00,
                                   urlImage = urlImage,
                                   thumbnail = config.thumbnail)

            await logChannel.send(embed=embedLog)
            await messageChannel.send(embed=embedMes)
            print(await message.channel.send('Валентинка успешно отправлена!'))

        if message.content.startswith(valentineCommandDeAnon):
            embedLog = createEmbed(title = "Новая заявка",
                                   description = 'Пользователь - <@{0}>\nСообщение - {1}\n'.format(UID, message.content.split(valentineCommandDeAnon)[1]),
                                   color = 0x00ff00,
                                   urlImage = urlImage)

            embedMes = createEmbed(title = "Новая валентика",
                                   description = 'Пользователь - <@{0}>\nСообщение - {1}\n'.format(UID, message.content.split(valentineCommandDeAnon)[1]),
                                   color = 0x00ff00,
                                   urlImage = urlImage)

            await logChannel.send(embed=embedLog)
            await messageChannel.send(embed=embedMes)
            await message.channel.send('Валентинка успешно отправлена!')

        if message.content.startswith(simpleMesageCommand):
            logChannel = client.get_channel(346775939709009920)
            await logChannel.send(message.content.split(simpleMesageCommand)[1])


    except AttributeError:
        pass

    except Exception as e:
        LOGGER.exception('Exception: ' + str(e))



client.run(config.token)

#346775939709009920
#member = await guild.fetch_member(UID)
