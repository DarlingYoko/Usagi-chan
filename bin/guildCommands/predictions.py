from random import randint


async def predict(self, message):
    try:
        content = message.content[15:].strip()
        if content[-1] == '?':
            content = content[:-1]

        if randint(0, 1):
            answer = '<@{0}> Я считаю, что {1} точно стоит!'.format(message.author.id, content)
        else:
            answer = '<@{0}> Я считаю, что {1} точно не стоит, бака!'.format(message.author.id, content)

        await message.channel.send(answer)
    except Exception as e:
        print(e)
