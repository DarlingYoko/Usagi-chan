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

async def pickColor(self, messageId, userId, emoji):

    colors = {667431391918555174: 858002295794696192,
                667431417973702666: 858002401746485249,
                667431463024590894: 858002623315050516,
                667431510307241984: 858003078707281950,
                667431579530035200: 858003180810272768,
                667431676627910687: 858003282860834897,
                667431704868290578: 858003617461567528,
                667431741736353803: 858004298808688640,
                667431773659201578: 858004563230982144,
                667431996104114198: 858004701663461426,
                667432024604409869: 858005872265396224,
                667432051896483842: 858008075537481749,
                667432082603114497: 858005242229948466,
                667432127893209098: 858005498799194143,}
    if messageId == 858003173947211816:
        if emoji.id in colors.keys():
            guild = await self.client.fetch_guild(self.config['data']['guildId'])
            role = guild.get_role(colors[emoji.id])
            user = await guild.fetch_member(userId)
            await user.remove_roles(role)


async def dellEmoji(self, payload):


    messageId = payload.message_id
    userId = payload.user_id
    emoji = payload.emoji
    channelId = payload.channel_id

    colorRoles = [667431391918555174,
                    667431417973702666,
                    667431463024590894,
                    667431510307241984,
                    667431579530035200,
                    667431676627910687,
                    667431704868290578,
                    667431741736353803,
                    667431773659201578,
                    667431996104114198,
                    667432024604409869,
                    667432051896483842,
                    667432082603114497,
                    667432127893209098]

    sheduleEmoji = self.client.get_emoji(810182035955777576)

    if sheduleEmoji == emoji and str(channelId) == self.config['sheduleData']['sheduleChannel']:
        checkRemoveNotification(self, messageId, userId)

    if '⛏️' ==  str(emoji) and str(channelId) == self.config['requestsData']['getRoleChannel']:
        await removeRequestsRole(self, messageId, userId)

    if emoji.id in colorRoles:
        await pickColor(self, messageId, userId, emoji)
        return

    try:
        #print(type(channelId), type(self.config['requestsData']['channel']))
        if channelId != self.config['requestsData'].getint('channel'):
            return
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
    newEmbed = createEmbed(description = '\n'.join(splitEmbed), thumbnail = embed['thumbnail']['url'], footer = embed['footer']['text'],
                            authorName = embed['author']['name'], authorIconURL = embed['author']['icon_url'], color = embed['color'])
    await msg.edit(embed = newEmbed)
