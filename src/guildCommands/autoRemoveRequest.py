from datetime import datetime, timedelta
from src.functions import createEmbed, newLog
import sys

async def autoRemoveRequest(self):
    requestsList = self.db.getAll(tableName = 'emojiData')
    for (msgId, helpers, time, author) in requestsList:
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

        msgIds = self.db.getValue(tableName = 'requestsData', argument = 'requests_ids', selector = 'user_id', value = author)
        if msgIds:
            msgIds = eval(msgIds)
        else:
            return
        msgIds.remove(int(msgId))
        if len(msgIds) == 0:
            self.db.remove(tableName = 'requestsData', selector = 'user_id', value = author)
        else:
            self.db.update(tableName = 'requestsData', argument = 'requests_ids', selector = 'user_id', newValue = str(msgIds), findValue = author)

        self.db.remove(tableName = 'emojiData', selector = 'request_id', value = msgId)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        newLog(exc_type, exc_obj, exc_tb, e)
    return
