from src.functions import createEmbed, newLog
import shelve, sys


def setNewReactionEvent(self):
    @self.client.event
    async def on_raw_reaction_add(payload):
        if payload.user_id == self.config['usersIDs'].getint('botId'):
            return
        await fillEmoji(self, payload)


async def fillEmoji(self, payload):
    try:
        accessEmoji = {'2️⃣': 2, '3️⃣': 3, '4️⃣': 4}

        messageId = payload.message_id
        userId = payload.user_id
        emoji = payload.emoji
        channelId = payload.channel_id

        channel = self.client.get_channel(channelId)
        msg = await channel.fetch_message(messageId)
        try:
            embed = msg.embeds[0].to_dict()
        except:
            return


        msgIds = self.db.get(userId = userId, table = 'requestsData')
        emojiIds = self.db.get(userId = messageId, table = 'emojiData')


        # проверка на существование заявки
        if emojiIds:
            timeEmoji = eval(emojiIds)
        else:
            return

        # проверка на эмодзи + создателя заявки
        if '🔒' == str(emoji):
            if msgIds:
                msgIds = eval(msgIds)
                if messageId in msgIds:
                    guild = await self.client.fetch_guild(payload.guild_id)
                    user = await guild.fetch_member(userId)
                    newEmbed = createEmbed(description = '~~' + embed['description'] + '~~', thumbnail = embed['thumbnail']['url'], footer = embed['footer']['text'], authorName = '{0} закрыл заявку.'.format(user.display_name), authorIconURL = embed['author']['icon_url'])
                    await msg.edit(content = None, embed = newEmbed)
                    await msg.unpin()

                    msgIds.remove(messageId)
                    if len(msgIds) == 0:
                        self.db.remove(userId = userId, table = 'requestsData')
                    else:
                        self.db.update(userId = userId, messageId = msgIds, table = 'requestsData')

                    self.db.remove(userId = messageId, table = 'emojiData')
                    return

            if userId != self.config['usersIDs']['botId']:
                await msg.remove_reaction(emoji = emoji, member = payload.member)
            return


        # Проверка на любой эмоджи от создателя заявки
        if msgIds:
            msgIds = eval(msgIds)

            if messageId in msgIds:
                await msg.remove_reaction(emoji = payload.emoji, member = payload.member)
                return

        # Проверка на доступные эмодзи от любого другого пользователя кроме создателя заявки
        if str(emoji) in accessEmoji.keys():
            timeEmoji = await addReaction(self, accessEmoji[str(emoji)], timeEmoji, msg, payload, embed)

            if timeEmoji:
                self.db.update(userId = messageId, messageId = timeEmoji, table = 'emojiData')
            return


        # Очищечние эмодзи если заявка есть, но эмодзи не доступен
        if str(emoji) not in accessEmoji.keys():
            await msg.remove_reaction(emoji = payload.emoji, member = payload.member)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        newLog(exc_type, exc_obj, exc_tb, e)



async def addReaction(self, id, timeEmoji, msg, payload, embed):
    if id not in timeEmoji.keys():
        if payload.user_id in timeEmoji.values() and payload.user_id != self.config['usersIDs']['botId']:
            await msg.remove_reaction(emoji = payload.emoji, member = payload.member)
            return 0
        else:
            timeEmoji[id] = payload.user_id
            await addInEmbed(id, msg, payload, embed)
    else:
        if payload.user_id != self.config['usersIDs']['botId']:
            await msg.remove_reaction(emoji = payload.emoji, member = payload.member)
            return 0

    return timeEmoji

async def addInEmbed(id, msg, payload, embed):
    newUser = '***{0}) Слот:** <@{1}>*'.format(id, payload.user_id)
    splitEmbed = embed['description'].split('\n')
    splitEmbed[3 + id] = newUser
    newEmbed = createEmbed(description = '\n'.join(splitEmbed), thumbnail = embed['thumbnail']['url'], footer = embed['footer']['text'], authorName = embed['author']['name'], authorIconURL = embed['author']['icon_url'])
    await msg.edit(embed = newEmbed)
