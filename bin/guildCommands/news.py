from datetime import datetime as dt

async def postNews(self):
    channel = await self.client.fetch_channel(863159302213337179)

    now = dt.now()
    if not self.time:
        return
    d = self.time - now
    hours = d.seconds // 3600
    minutes = (d.seconds - (hours * 3600)) // 60

    daysStr = 'дней'
    if d.days == 1:
        daysStr = 'день'
    elif d.days >= 2 and d.days <= 4:
        daysStr = 'дня'

    hoursStr = 'часов'
    if hours % 10 == 1 and hours != 11:
        hoursStr = 'час'
    elif hours % 10 >= 2 and hours % 10 <= 4 and hours not in [12, 13, 14]:
        hoursStr = 'часа'

    await channel.edit(name = '{0} {3} {1} {4} {2} мин'.format(d.days, hours, minutes, daysStr, hoursStr))


async def setTime(self, message):

    answer = 'Не получилось установить время, бака!'
    try:
        content = message.content.split('!время')[1].strip()
        self.time = dt.strptime(content, '%d.%m.%y %H:%M')
        answer = 'Новое время утсановлено, нья!'
    except Exception as e:
        print(e)

    await message.channel.send(answer)
