from datetime import datetime

async def forum(self):
    if datetime.now().hour == 17 and (datetime.now().minute > 0 and datetime.now().minute < 15):
        channel = await self.client.fetch_channel(858053937008214018)
        await channel.send('Не забываем забрать логин бонус!\nhttps://webstatic-sea.mihoyo.com/ys/event/signin-sea/index.html?act_id=e202102251931481&lang=ru-ru')
