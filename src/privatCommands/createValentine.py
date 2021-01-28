from src.functions import *
import src.config as config
import shelve, discord

def getType(input):
    if input == 'я':
        return 1
    elif input == 'рандом':
        return 2
    else:
        return input



async def valentineCommand(data, members):
    valentineData = shelve.open('db/valentineData')
    logChannel = data['client'].get_channel(config.logChannel)
    messageChannel = data['client'].get_channel(config.messageChannel)
    guild = await data['client'].fetch_guild(config.serverID)
    countValentine = 0
    msg = message.content.split(splitStr)[1].split('/')
    if len(msg) < 3 or len(msg) > 3:
        answer = '''Неправильный формат валентинки. Прочтите синтаксис!
        :round_pushpin: Использование: `!валентинка <от кого>/<кому>/<сообщение>`
        :round_pushpin: Пример: `!валентинка я/@Raiva#7811/Люблю Райву!!`
        **ПРИМЕЧАНИЕ**: Все поля обязательно должны быть заполнены и разделены `/`'''
        embed = createEmbed(description = answer)
        await message.channel.send('<@{0}>'.format(UID), embed = embed)
        return

    try:
        countValentine = valentineData[str(UID)]['count'] + 1
        data = valentineData[str(UID)]
    except:
        countValentine = 1
        data = {}


    type = getType(msg[0])
    forUser = members.findByName()
    content = msg[2]

    print(type, forUser, content)
    '''
    title = 'Анонимная валентинка!'
    answer = 'Анонимная валентинка #{0}, успешно отправлена!'.format(countValentine)
    if not anon:
        title = 'Валентинка от Тухеда <:2Head:771044700630548520>!'.format(message.author.display_name)
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
    msgData = await messageChannel.send('<@290166276796448768>', embed=embedMes)

    data['count'] = countValentine
    data[countValentine] = msgData.id
    valentineData[str(UID)] = data
    '''
    valentineData.close()
