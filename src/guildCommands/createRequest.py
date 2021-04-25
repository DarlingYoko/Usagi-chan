from src.functions import wrongMessage, getCurrentTime, createEmbed, newLog
from time import mktime
from datetime import datetime
import sys



async def createRequest(self, data):
    try:
        if data['message'].channel.id != self.config['requestsData'].getint('channel'):
            title = 'В этом канале нельзя использовать эту команду!'
            description = 'Вам сюда 👉 <#{0}>'.format(self.config['requestsData']['channel'])
            await wrongMessage(data = data, title = title, description = description)
            return


        msg = data['content'].split('/')
        messageChannel = self.client.get_channel(self.config['requestsData'].getint('channel'))
        counter = {2: '2️⃣', 3: '3️⃣', 4: '4️⃣'}
        serversId = {6: 'Америка', 7: 'Европа', 8: 'Азия', 9: 'Тайвань'}

        if len(msg) < 4 or len(msg) > 4:
            title = 'Неправильный формат запроса. Прочтите синтаксис!'
            description = ''':round_pushpin: Использование: `!создать <world>/<id>/<slots>/<message>`
                             :round_pushpin: Пример: `!создать 7/7000563212/3/Фармим рофлочурлов`
                             **ПРИМЕЧАНИЕ**: Все поля обязательно должны быть заполнены и разделены `/`'''
            await wrongMessage(data = data, title = title, description = description, delay = 60)
            return

        try:
            lvlWorld = int(msg[0])
            if lvlWorld > 8 or lvlWorld < 1:
                title = 'Неверный уровень мира!'
                description = '**Уровень мира** не может быть больше `8` или меньше `1`'
                await wrongMessage(data = data, title = title, description = description)
                return
        except:
            title = 'Неверный уровень мира!'
            description = 'Проверьте формат **уровня мира**, он должен состоять из одной цифры от `1` до `8`'
            await wrongMessage(data = data, title = title, description = description)
            return


        try:
            length = len(msg[1])
            UID = int(msg[1])
            if length > 9 or length < 9:
                title = 'Неверный UID!'
                description = '**UID** не может содержать больше `9` цифр'
                await wrongMessage(data = data, title = title, description = description)
                return

            firstSymbol = int(msg[1][0])
            if firstSymbol not in serversId.keys():
                title = 'Неверный UID!'
                description = 'Сервера с таким **UID** не существует, проверьте **UID**.'
                await wrongMessage(data = data, title = title, description = description)
                return

            server = serversId[firstSymbol]

        except:
            title = 'Неверный UID!'
            description = 'Проверьте формат **UID**, он должен состоять из девяти цифр'
            await wrongMessage(data = data, title = title, description = description)
            return

        try:
            numberOfSlots = int(msg[2])
            if numberOfSlots > 3 or numberOfSlots < 1:
                title = 'Неверное количество слотов!'
                description = 'Их может быть не больше `3` и не меньше `1`'
                await wrongMessage(data = data, title = title, description = description)
                return
        except:
            title = 'Неверный формат слотов!'
            description = 'Проверьте формат **слота**, он должен состоять из одной цифры от `1` до `3`'
            await wrongMessage(data = data, title = title, description = description)
            return

        text = msg[3]
        slots = '***1) Слот:** <@{0}>*\n'.format(data['message'].author.id)



        for i in range(numberOfSlots):
            slots += '***{0}) Слот:** Пусто*\n'.format(i + 2)


        authorName = '{0} создаёт новую заявку.'.format(data['message'].author.display_name)
        authorIconURL = data['message'].author.avatar_url
        description = ':park: **Мир:** {0} уровня\n:label: **UID:** {1}\n:map: **Сервер:** {4}\n:busts_in_silhouette: **Слоты:**\n{3}:pencil: **Описание:** {2}'.format(lvlWorld, UID, text, slots, server)
        footer = 'Заявка создана в {0} по МСК'.format(getCurrentTime())
        time = mktime(datetime.now().timetuple())

        embed = createEmbed(description = description, thumbnail = self.config['requestsData']['thumbnail'], footer = footer, authorName = authorName, authorIconURL = authorIconURL, color = 0xf08080)
        timeMsg = await messageChannel.send('<@&{}>'.format(self.config['requestsData']['roleID']), embed = embed)

        await timeMsg.add_reaction('🔒')
        for i in range(numberOfSlots):
            await timeMsg.add_reaction(counter[i + 2])

        try:
            await timeMsg.pin()
        except:
            pass



        userId = data['message'].author.id
        msgIds = self.db.getValue(tableName = 'requestsData', argument = 'requests_ids', selector = 'user_id', value = userId)
        if msgIds:
            msgIds = eval(msgIds)
            msgIds.append(timeMsg.id)
            self.db.update(tableName = 'requestsData', argument = 'requests_ids', selector = 'user_id', newValue = str(msgIds), findValue = userId)

        else:
            msgIds = [timeMsg.id]
            self.db.insert('requestsData', userId, str(msgIds))

        self.db.insert('emojidata', timeMsg.id, str({}), time, userId)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        newLog(exc_type, exc_obj, exc_tb, e)
