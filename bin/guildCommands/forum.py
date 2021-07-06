from datetime import datetime, timedelta
from time import mktime

async def forum(self):
    if datetime.now().hour == 16:
        channel = await self.client.fetch_channel(858053937008214018)
        channel = await self.client.fetch_channel(858093764408508436)
        await channel.send('Не забываем забрать логин бонус!\nhttps://webstatic-sea.mihoyo.com/ys/event/signin-sea/index.html?act_id=e202102251931481&lang=ru-ru')


async def checkTransform(self):
    usersList = self.db.getAll(tableName = 'forum')
    for (userID, time) in usersList:
        time = datetime.fromtimestamp(float(time))

        if datetime.now() - time >= timedelta(days = 6, hours = 22):
            channel = await self.client.fetch_channel(859772440195760178)
            await channel.send('<@{0}> Преобразователь готов, нья!'.format(userID))
            time = mktime(datetime.now().timetuple())
            self.db.update('forum', 'time', 'userid', time, userID)


async def transform(self, message):

    if message.channel.id != 859772440195760178:
        await message.channel.send('Эта команда для канала <#{0}>, бака!'.format(859772440195760178, delete_after = 30))
        await message.delete()
        return


    content = message.content.split('!преобразователь')[1].strip().split()
    answer = '<@{0}> Неверная команда, бака!'

    #print(content, content[0], len(content), content and content[0] == 'добавить')

    if content and content[0] == 'добавить':
        #только что юз и кд неделя
        time = mktime(datetime.now().timetuple())

        #имеется какое то время для отката
        if len(content) != 1:
            try:
                delta = 166 - int(content[1])
                time = mktime((datetime.now() - timedelta(hours = delta)).timetuple())
            except Exception as e:
                print(e)
                answer = '<@{0}> Неправильный формат времени, бака!'

        try:
            self.db.insert('forum', message.author.id, time)
            answer = '<@{0}> Успешно добавлено, нья!'
        except Exception as e:
            print(e)
            answer = '<@{0}> Не получилось добавить'

    #удалить отслеживание пользователя
    elif content and content[0] == 'удалить':
        try:
            self.db.remove('forum', 'userID', message.author.id)
            answer = '<@{0}> Успешно удалено, нья!'
        except Exception as e:
            print(e)
            answer = '<@{0}> Не получилось удалить'

    await message.channel.send(answer.format(message.author.id))


    #time = mktime(datetime.now().timetuple())
