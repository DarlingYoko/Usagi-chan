from src.functions import *
import src.config as config
import shelve

async def valentineCommand(client, message, UID, splitStr, urlImage = None, anon = True):
    valentineData = shelve.open('db/valentineData')
    msg = message.content.split(splitStr)[1]
    logChannel = client.get_channel(config.logChannel)
    messageChannel = client.get_channel(config.messageChannel)
    countValentine = 0

    try:
        countValentine = valentineData[str(UID)]['count'] + 1
        data = valentineData[str(UID)]
    except:
        countValentine = 1
        data = {}

    title = 'Анонимная валентинка!'
    answer = 'Анонимная валентинка #{0}, успешно отправлена!'.format(countValentine)
    if not anon:
        title = 'Валентинка от {0}!'.format(message.author.display_name)
        answer ='Не анонимная валентинка #{0}, успешно отправлена!'.format(countValentine)

    embedLog = createEmbed(title = "Новая заявка",
                           description = '**Пользователь** - <@{0}>\n**Сообщение** - {1}\n'.format(UID, msg),
                           color = 0x00ff00,
                           urlImage = urlImage)

    embedMes = createEmbed(title = title,
                           description = '{1}\n'.format(UID, msg),
                           color = 0x00ff00,
                           urlImage = urlImage,
                           thumbnail = config.thumbnail)

    await logChannel.send(embed=embedLog)
    await message.channel.send(answer, embed=embedMes)
    msgData = await messageChannel.send(embed=embedMes)

    data['count'] = countValentine
    data[countValentine] = msgData.id
    valentineData[str(UID)] = data
    valentineData.close()


async def deleteValentine(client, message, UID, splitStr):
    valentineData = shelve.open('db/valentineData')
    messageChannel = client.get_channel(config.messageChannel)
    answer = 'Неправильный формат(('
    try:
        msg = int(message.content.split(splitStr)[1])
        idValentine = valentineData[str(UID)][msg]
        msg = await messageChannel.fetch_message(idValentine)
        await msg.delete()
        answer = 'Успешно удалено!'
    except:
        pass

    await message.channel.send(answer)
