import aiohttp, sys

async def createNewEmoji(self, message):
    if message.channel.id != self.config['data'].getint('getEmojiChannel'):
        await message.channel.send('<@{1}> Эта команда для канала <#{0}>'.format(self.config['data'].getint('getEmojiChannel'), message.author.id), delete_after = 30)
        await message.delete()
        return

    if not message.attachments:
        await message.channel.send('<@{0}> Ты не прикрепил аттачмет! Баака'.format(message.author.id), delete_after = 30)
        await message.delete()
        return



    try:
        guild = await self.client.fetch_guild(self.config['data']['guildId'])
        name = message.content.split('!эмодзи')[1].strip()
        image = message.attachments[0]
        async with aiohttp.ClientSession() as session:
            async with session.get(str(image)) as response:
                img = await response.read()
                await guild.create_custom_emoji(name = name, image = img)
        await message.channel.send('<@{0}> Добавила'.format(message.author.id))
    except Exception as e:
        await message.channel.send('<@{0}> Не получилось создать('.format(message.author.id))
        print('При создании роли ошибка\n', e)
