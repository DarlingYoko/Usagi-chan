import aiohttp, sys

async def createNewEmoji(self, message):
    if message.channel.id != self.config['data'].getint('getEmojiChannel'):
        await message.channel.send('Эта команда для канала <#{0}>'.format(self.config['data'].getint('getEmojiChannel')), delete_after = 30)
        await message.delete()
        return

    if not message.attachments:
        await message.channel.send('Ты не прикрепил аттачмет! Баака', delete_after = 30)
        await message.delete()
        return

    guild = await self.client.fetch_guild(self.config['data']['guildId'])
    name = message.content.split('!эмодзи')[1].strip()



    image = message.attachments[0]

    async with aiohttp.ClientSession() as session:
        async with session.get(str(image)) as response:
            img = await response.read()
            await guild.create_custom_emoji(name = name, image = img)
