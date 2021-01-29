from datetime import datetime, timedelta
import src.config as config
from src.functions import createEmbed, newLog

async def autoRemoveRequest(db, client):
    requestsList = db.getTime()
    for (msgId, time, author) in requestsList:
        time = datetime.fromtimestamp(float(time))
        if datetime.now() - time > timedelta(seconds = 10):#(hours = 6):
            await removeRequest(db, client, msgId, author)


async def removeRequest(db, client, msgId, author):
    try:
        guild = await client.fetch_guild(config.puficonfaId)
        channel = await client.fetch_channel(config.requestChannel)
        user = await guild.fetch_member(author)
        msg = await channel.fetch_message(msgId)
        embed = msg.embeds[0].to_dict()


        newEmbed = createEmbed(description = '~~' + embed['description'] + '~~', thumbnail = embed['thumbnail']['url'], footer = embed['footer']['text'], authorName = '{0} закрыл заявку.'.format(user.display_name), authorIconURL = embed['author']['icon_url'])
        await msg.edit(content = None, embed = newEmbed)
        await msg.unpin()

        msgIds = db.get(userId = author, table = 'requestsData')
        if msgIds:
            msgIds = eval(msgIds)
        else:
            return
        msgIds.remove(int(msgId))
        if len(msgIds) == 0:
            db.remove(userId = author, table = 'requestsData')
        else:
            db.update(userId = author, messageId = msgIds, table = 'requestsData')

        db.remove(userId = msgId, table = 'emojiData')

    except Exception as e:
        newLog('New error in auto remove request at {1}:\n{0}'.format(e, datetime.datetime.now()))
    return
