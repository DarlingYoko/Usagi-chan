from src.functions import createEmbed
#!remove 846665748754595842

async def manualRemoveRequest(self, message, id):
    removeMessage = await message.channel.fetch_message(id)
    try:
        embed = removeMessage.embeds[0].to_dict()
    except:
        print('Не удалось получить ембед')

    newEmbed = createEmbed(description = '~~' + embed['description'] + '~~', thumbnail = embed['thumbnail']['url'], footer = embed['footer']['text'],
                            authorName = embed['author']['name'][:-22] + ' закрыл заявку.', authorIconURL = embed['author']['icon_url'], color = embed['color'])
    await removeMessage.edit(content = None, embed = newEmbed)
    await removeMessage.unpin()

    author = self.db.getValue(tableName = 'emojidata', argument = 'author', selector = 'request_id', value = id)
    self.db.remove(tableName = 'emojidata', selector = 'request_id', value = id)


    request_ids = self.db.getValue(tableName = 'requestsdata', argument = 'requests_ids', selector = 'user_id', value = author)
    request_ids = eval(request_ids)
    request_ids.remove(int(id))
    self.db.update(tableName = 'requestsdata', argument = 'requests_ids', selector = 'user_id', newValue = str(request_ids), findValue = author)
