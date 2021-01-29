from src.functions import createEmbed, newLog
import src.config as config
import shelve, datetime


def setNewReactionEvent(self):
    @self.client.event
    async def on_raw_reaction_add(payload):
        if payload.guild_id == 346775939105161247: # УББРАТЬ ПРИ ДЕПЛОЕ
            return
        if payload.user_id == config.botId:
            return
        await fillEmoji(payload, self.client, self.db)


async def fillEmoji(payload, client, db):
    try:
        accessEmoji = ['🔒', '2️⃣', '3️⃣', '4️⃣']

        messageId = payload.message_id
        userId = payload.user_id
        emoji = payload.emoji
        channelId = payload.channel_id

        channel = client.get_channel(channelId)
        msg = await channel.fetch_message(messageId)
        try:
            embed = msg.embeds[0].to_dict()
        except:
            return
        #print(emoji)


        msgIds = db.get(userId = userId, table = 'requestsData')
        emojiIds = db.get(userId = messageId, table = 'emojiData')
        if '🔒' == str(emoji):
            if msgIds:
                msgIds = eval(msgIds)
                if messageId in msgIds:
                    guild = await client.fetch_guild(payload.guild_id)
                    user = await guild.fetch_member(userId)
                    newEmbed = createEmbed(description = '~~' + embed['description'] + '~~', thumbnail = embed['thumbnail']['url'], footer = embed['footer']['text'], authorName = '{0} закрыл заявку.'.format(user.display_name), authorIconURL = embed['author']['icon_url'])
                    await msg.edit(content = None, embed = newEmbed)
                    await msg.unpin()

                    msgIds.remove(messageId)
                    if len(msgIds) == 0:
                        db.remove(userId = userId, table = 'requestsData')
                    else:
                        db.update(userId = userId, messageId = msgIds, table = 'requestsData')

                    db.remove(userId = messageId, table = 'emojiData')
                    return


            if userId != config.botId:
                await msg.remove_reaction(emoji = emoji, member = payload.member)
            return


        if emojiIds:
            if msgIds:
                msgIds = eval(msgIds)
                if messageId in msgIds:
                    await msg.remove_reaction(emoji = payload.emoji, member = payload.member)
                    return

            timeEmoji = eval(emojiIds)
            if '2️⃣' == str(emoji):
                timeEmoji = await addReaction(2, timeEmoji, msg, payload, embed)

            if '3️⃣' == str(emoji):
                timeEmoji = await addReaction(3, timeEmoji, msg, payload, embed)

            if '4️⃣' == str(emoji):
                timeEmoji = await addReaction(4, timeEmoji, msg, payload, embed)

            db.update(userId = messageId, messageId = timeEmoji, table = 'emojiData')

        if str(emoji) not in accessEmoji:
            await msg.remove_reaction(emoji = payload.emoji, member = payload.member)
    except Exception as e:
        newLog('New error in new reaction event at {1}:\n{0}'.format(e, datetime.datetime.now()))



async def addReaction(id, timeEmoji, msg, payload, embed):
    if id not in timeEmoji.keys():
        if payload.user_id in timeEmoji.values() and payload.user_id != config.botId:
            await msg.remove_reaction(emoji = payload.emoji, member = payload.member)
        else:
            timeEmoji[id] = payload.user_id
            await addInEmbed(id, msg, payload, embed)
    else:
        if payload.user_id != config.botId:
            await msg.remove_reaction(emoji = payload.emoji, member = payload.member)

    return timeEmoji

async def addInEmbed(id, msg, payload, embed):
    newUser = '***{0}) Слот:** <@{1}>*'.format(id, payload.user_id)
    splitEmbed = embed['description'].split('\n')
    splitEmbed[3 + id] = newUser
    newEmbed = createEmbed(description = '\n'.join(splitEmbed), thumbnail = embed['thumbnail']['url'], footer = embed['footer']['text'], authorName = embed['author']['name'], authorIconURL = embed['author']['icon_url'])
    await msg.edit(embed = newEmbed)
