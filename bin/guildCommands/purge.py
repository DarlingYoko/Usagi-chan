


async def purge(self, message):
    try:
        content = int(message.content.split('!purge')[1].strip())
        history = await message.channel.history(limit = content).flatten()
        for msg in history:
            await msg.delete()
    except Exception as e:
        print(e)
    await message.channel.send('Удалила', delay = 10)
