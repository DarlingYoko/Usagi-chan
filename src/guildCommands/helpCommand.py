import src.config as config
from src.functions import createEmbed, newLog
import datetime

async def helpCommand(data):
    try:
        if data['message'].channel.id != config.logChannel:
            title = 'В этом канале нельзя использовать эту команду!'
            description = 'Вам сюда 👉 <#{0}>'.format(config.logChannel)
            await wrongMessage(data = data, title = title, description = description)
            await data['message'].delete()
            return
        title = 'Справка'
        description = '''> <@&803376059776368671> - **автороль созданная для получения оповещений и создания заявок, в канале** <#771469144938905641>

                        :meat_on_bone: **Получить роль** можно, в канале <#774283496755036180> и нажмите на :pick: **под последним сообщением.**
                        :poultry_leg: **Для создания заявки** в канале <#771469144938905641> вам нужно указать;
                        !создать `уровень мира`/`ваш уид`/`количество слотов свободных в пати`/`описание`
                        :poultry_leg: **Для закрытия** заявки вам нужно нажать на :lock: под **вашей** заявкой

                        `Все подробности и примеры в канале `<#774283496755036180> `в последнем посте.`'''
        thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/803383108484595762/unknown.png'
        embed = createEmbed(title = title, description = description, thumbnail = thumbnail)
        await data['message'].channel.send(embed = embed, delete_after = 60)
        await data['message'].delete()
    except Exception as e:
        newLog('New error in help command at {1}:\n{0}'.format(e, datetime.datetime.now()))
