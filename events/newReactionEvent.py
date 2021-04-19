from src.functions import createEmbed, newLog
import shelve, sys


def setNewReactionEvent(self):
    @self.client.event
    async def on_raw_reaction_add(payload):
        if payload.user_id == self.config['usersIDs'].getint('botId'):
            return
        await fillEmoji(self, payload)

def checkNewNotification(self, messageId, userId):
    users = self.db.getValue(tableName = 'shedule', argument = 'users', selector = 'messageId', value = messageId)
    users = eval(users)
    if userId not in users:
        users.append(userId)
        self.db.update(tableName = 'shedule', argument = 'users', selector = 'messageId', newValue = users, findValue = messageId)

async def giveRequestsRole(self, messageId, userId):
    if str(messageId) == self.config['requestsData']['getRoleMessage']:
        guild = await self.client.fetch_guild(self.config['data']['guildId'])
        role = guild.get_role(int(self.config['requestsData']['roleID']))
        user = await guild.fetch_member(userId)
        await user.add_roles(role)





async def fillEmoji(self, payload):

    messageId = payload.message_id
    userId = payload.user_id
    emoji = payload.emoji
    channelId = payload.channel_id

    sheduleEmoji = self.client.get_emoji(810182035955777576)


    if sheduleEmoji == emoji and str(channelId) == self.config['sheduleData']['sheduleChannel']:
        checkNewNotification(self, messageId, userId)

    if '⛏️' ==  str(emoji) and str(channelId) == self.config['requestsData']['getRoleChannel']:
        await giveRequestsRole(self, messageId, userId)


    try:
        accessEmoji = {'2️⃣': 2, '3️⃣': 3, '4️⃣': 4}
        channel = self.client.get_channel(channelId)
        msg = await channel.fetch_message(messageId)
        try:
            embed = msg.embeds[0].to_dict()
        except:
            return



        msgIds = self.db.getValue(tableName = 'requestsData', argument = 'requests_ids', selector = 'user_id', value = userId)
        emojiIds = self.db.getValue(tableName = 'emojiData', argument = 'helper_ids', selector = 'request_id', value = messageId)


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
                        self.db.remove(tableName = 'requestsData', selector = 'user_id', value = userId)
                    else:
                        self.db.update(tableName = 'requestsData', argument = 'requests_ids', selector = 'user_id', newValue = str(msgIds), findValue = userId)

                    self.db.remove(tableName = 'emojiData', selector = 'request_id', value = messageId)
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
                self.db.update(tableName = 'emojiData', argument = 'helper_ids', selector = 'request_id', newValue = str(timeEmoji), findValue = messageId)
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
