
async def checkHistory(self, incoming, command):
    print(1)
    messages = await incoming.channel.history(limit=None).flatten()
    content = incoming.content.split(command)[1].strip()
    i = 0
    print(len(messages))
    for message in messages:
        if message.author.id == incoming.author.id and content in message.content:
            i += 1
    answer = 'раз'
    if i%10 >= 2 and i%10 <= 4:
        answer += 'а'
    await incoming.channel.send('<@{0}> заспамил "{1}" {4} {2} в канале <#{3}>'.format(incoming.author.id, content, answer, incoming.channel.id, i))
