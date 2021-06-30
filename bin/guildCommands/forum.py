from datetime import datetime, timedelta
from time import mktime

async def forum(self):
    print(datetime.now().hour, datetime.now().minute)
    print(datetime.now().hour == 17 and (datetime.now().minute > 0 and datetime.now().minute < 30))
    if datetime.now().hour == 17 and (datetime.now().minute > 0 and datetime.now().minute < 30):
        channel = await self.client.fetch_channel(858053937008214018)
        await channel.send('Не забываем забрать логин бонус!\nhttps://webstatic-sea.mihoyo.com/ys/event/signin-sea/index.html?act_id=e202102251931481&lang=ru-ru')


async def checkTransform(self):
    usersList = self.db.getAll(tableName = 'forum')
    for (userID, time) in usersList:
        time = datetime.fromtimestamp(float(time))

        if datetime.now() - time >= timedelta(days = 7):
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
    answer = 'Неверная команда, бака!'

    #print(content, content[0], len(content), content and content[0] == 'добавить')

    if content and content[0] == 'добавить':
        #только что юз и кд неделя
        time = mktime(datetime.now().timetuple())
        if len(content) == 1:
            try:
                self.db.insert('forum', message.author.id, time)
                answer = 'Успешно добавлено, нья!'
            except Exception as e:
                print(e)
                answer = 'Не получилось добавить'

        #имеется какое то время для отката
        else:
            pass

    #удалить отслеживание пользователя
    elif content and content[0] == 'удалить':
        try:
            self.db.remove('forum', 'userID', message.author.id)
            answer = 'Успешно удалено, нья!'
        except Exception as e:
            print(e)
            answer = 'Не получилось удалить'

    await message.channel.send(answer)


    #time = mktime(datetime.now().timetuple())
