from src.functions import createEmbed, newLog
import shelve, sys

def setRemoveReactionEvent(self):
    @self.client.event
    async def on_raw_reaction_remove(payload):
        if payload.user_id == self.config['usersIDs'].getint('botId'):
            return
        await dellEmoji(self, payload)


def checkRemoveNotification(self, messageId, userId):
    users = self.db.getValue(tableName = 'shedule', argument = 'users', selector = 'messageId', value = messageId)
    users = eval(users)
    if userId in users:
        users.remove(userId)
        self.db.update(tableName = 'shedule', argument = 'users', selector = 'messageId', newValue = users, findValue = messageId)

async def removeRequestsRole(self, messageId, userId):
    if str(messageId) == self.config['requestsData']['getRoleMessage']:
        guild = await self.client.fetch_guild(self.config['data']['guildId'])
        role = guild.get_role(int(self.config['requestsData']['roleID']))
        user = await guild.fetch_member(userId)
        await user.remove_roles(role)


async def dellEmoji(self, payload):


    messageId = payload.message_id
    userId = payload.user_id
    emoji = payload.emoji
    channelId = payload.channel_id

    sheduleEmoji = self.client.get_emoji(810182035955777576)

    if sheduleEmoji == emoji and str(channelId) == self.config['sheduleData']['sheduleChannel']:
        checkRemoveNotification(self, messageId, userId)

    if '⛏️' ==  str(emoji) and str(channelId) == self.config['requestsData']['getRoleChannel']:
        await removeRequestsRole(self, messageId, userId)

    try:
        accessEmoji = {'2️⃣': 2, '3️⃣': 3, '4️⃣': 4}
        channel = self.client.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        try:
            embed = msg.embeds[0].to_dict()
        except:
            return
        emojiIds = self.db.getValue(tableName = 'emojiData', argument = 'helper_ids', selector = 'request_id', value = messageId)

        # проверка на существование заявки
        if emojiIds:
            timeEmoji = eval(emojiIds)
        else:
            return

        # Проверка на доступные эмодзи от любого другого пользователя кроме создателя заявки
        if str(emoji) in accessEmoji.keys():
            timeEmoji = await removeReaction(accessEmoji[str(emoji)], timeEmoji, msg, payload, embed)

            if timeEmoji != -1:
                self.db.update(tableName = 'emojiData', argument = 'helper_ids', selector = 'request_id', newValue = str(timeEmoji), findValue = messageId)
            return


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        newLog(exc_type, exc_obj, exc_tb, e)


async def removeReaction(id, timeEmoji, msg, payload, embed):

    if id in timeEmoji.keys() and timeEmoji[id] == payload.user_id:
        del timeEmoji[id]
        await removeFromEmbed(id, msg, embed)
        return timeEmoji

    return -1

async def removeFromEmbed(id, msg, embed):
    newUser = '***{0}) Слот:** Пусто*'.format(id)
    splitEmbed = embed['description'].split('\n')
    splitEmbed[3 + id] = newUser
    newEmbed = createEmbed(description = '\n'.join(splitEmbed), thumbnail = embed['thumbnail']['url'], footer = embed['footer']['text'], authorName = embed['author']['name'], authorIconURL = embed['author']['icon_url'])
    await msg.edit(embed = newEmbed)
