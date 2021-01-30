from src.functions import createEmbed, newLog
import src.config as config
import shelve

def setRemoveReactionEvent(self):
    @self.client.event
    async def on_raw_reaction_remove(payload):
        if payload.user_id == config.botId:
            return
        await dellEmoji(payload, self.client, self.db)



async def dellEmoji(payload, client, db):
    try:
        emoji = payload.emoji

        messageId = payload.message_id
        channel = client.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        try:
            embed = msg.embeds[0].to_dict()
        except:
            return
        emojiIds = db.get(userId = messageId, table = 'emojiData')
        if emojiIds:# and str(userId) not in requestsData.keys():
            timeEmoji = eval(emojiIds)
            if '2️⃣' == str(emoji):
                timeEmoji = await removeReaction(2, timeEmoji, msg, payload, embed)

            if '3️⃣' == str(emoji):
                timeEmoji = await removeReaction(3, timeEmoji, msg, payload, embed)

            if '4️⃣' == str(emoji):
                timeEmoji = await removeReaction(4, timeEmoji, msg, payload, embed)


            db.update(userId = messageId, messageId = timeEmoji, table = 'emojiData')
    except Exception as e:
        newLog('New error in remove reaction event at {1}:\n{0}'.format(e, datetime.datetime.now()))


async def removeReaction(id, timeEmoji, msg, payload, embed):

    if id in timeEmoji.keys() and timeEmoji[id] == payload.user_id:
        del timeEmoji[id]
        await removeFromEmbed(id, msg, embed)

    return timeEmoji

async def removeFromEmbed(id, msg, embed):
    newUser = '***{0}) Слот:** Пусто*'.format(id)
    splitEmbed = embed['description'].split('\n')
    splitEmbed[3 + id] = newUser
    newEmbed = createEmbed(description = '\n'.join(splitEmbed), thumbnail = embed['thumbnail']['url'], footer = embed['footer']['text'], authorName = embed['author']['name'], authorIconURL = embed['author']['icon_url'])
    await msg.edit(embed = newEmbed)
