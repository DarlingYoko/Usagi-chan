from src.functions import createEmbed, newLog, wrongMessage
import sys

async def helpCommand(self, data):
    try:
        if data['message'].channel.id != self.config['requestsData'].getint('channel'):
            title = 'В этом канале нельзя использовать эту команду!'
            description = 'Вам сюда 👉 <#{0}>'.format(self.config['requestsData']['channel'])
            await wrongMessage(data = data, title = title, description = description)
            await data['message'].delete()
            return
        title = 'Справка'
        description = ('> <@&{0}> - **автороль созданная для получения оповещений и создания заявок, в канале** <#{1}>\n'.format(self.config['requestsData']['roleID'], self.config['requestsData']['channel']) +
                        ':meat_on_bone: **Получить роль** можно, в канале <#{0}> и нажмите на :pick: **под последним сообщением.**\n'.format(self.config['data']['getRoleChannel']) +
                        ':poultry_leg: **Для создания заявки** в канале <#{0}> вам нужно указать;\n'.format(self.config['requestsData']['channel']) +
                        '!создать `уровень мира`/`ваш уид`/`количество слотов свободных в пати`/`описание`\n' +
                        ':poultry_leg: **Для закрытия** заявки вам нужно нажать на :lock: под **вашей** заявкой, но помните, что в ваша заявка будет **автоматически закрыта через 6 часов**.\n\n'
                        '`Все подробности и примеры в канале `<#{0}> `в последнем посте.`'.format(self.config['data']['getRoleChannel']))
        thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/803383108484595762/unknown.png'
        embed = createEmbed(title = title, description = description, thumbnail = thumbnail)
        await data['message'].channel.send(embed = embed, delete_after = 60)
        await data['message'].delete()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        newLog(exc_type, exc_obj, exc_tb, e)
