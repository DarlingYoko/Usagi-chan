from datetime import datetime, timedelta
from src.functions import createEmbed, newLog
import sys

async def autoRemoveRequest(self):
    requestsList = self.db.getTime()
    for (msgId, time, author) in requestsList:
        time = datetime.fromtimestamp(float(time))
        if datetime.now() - time > timedelta(hours = 6):
            await removeRequest(self, msgId, author)


async def removeRequest(self, msgId, author):
    try:
        guild = await self.client.fetch_guild(self.config['data']['guildId'])
        channel = await self.client.fetch_channel(self.config['requestsData']['channel'])
        user = await guild.fetch_member(author)
        msg = await channel.fetch_message(msgId)
        embed = msg.embeds[0].to_dict()


        newEmbed = createEmbed(description = '~~' + embed['description'] + '~~', thumbnail = embed['thumbnail']['url'], footer = embed['footer']['text'], authorName = '{0} закрыл заявку.'.format(user.display_name), authorIconURL = embed['author']['icon_url'])
        await msg.edit(content = None, embed = newEmbed)
        await msg.unpin()

        msgIds = self.db.get(userId = author, table = 'requestsData')
        if msgIds:
            msgIds = eval(msgIds)
        else:
            return
        msgIds.remove(int(msgId))
        if len(msgIds) == 0:
            self.db.remove(userId = author, table = 'requestsData')
        else:
            self.db.update(userId = author, messageId = msgIds, table = 'requestsData')

        self.db.remove(userId = msgId, table = 'emojiData')

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        newLog(exc_type, exc_obj, exc_tb, e)
    return
