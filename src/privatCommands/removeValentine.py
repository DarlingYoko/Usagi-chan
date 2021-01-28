
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
