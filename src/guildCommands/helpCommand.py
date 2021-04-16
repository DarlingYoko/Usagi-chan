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

        helpMsg = (':snail: **Для создания заявки вам нужно указать следующие параметры;**\n!создать `уровень мира`/`ваш уид`/`количество слотов свободных в пати`/`описание`\n\n' +
                        '**Пример**\n:YEP~1: `- Знач пишу `\n!создать 7/3724627346/3/Хочу пособирать руду. Нужны 3 добровольца. Всяким **Кисикам**:loveKeqing:  не заходить. \n:peepoG~1: `- Нажимаю клавишу enter.`\n:peepoPANTIES: `- Ура! Работаеть!`\n\n\n' +
                        '> :snail: **Для закрытия Заявки нужно:**\n\n:lock: Достаточно на **своей** же заявке нажать на реакцию :lock: и она закроется.\n:lock: **Если вы забывчивый человек**, то не переживайте, через 6 часов заявка закроется сама!\n\n' +
                        ':PepeLaugh~1:`- Фух, ну теперь то я точно закрою заявку!`\n\n' +
                        ':boom: **Очень важные примечания!** :boom:\n\n' +
                        ':ban:  **Все поля** должны быть заполнены и разделены слешем `/`.\n' +
                        ':ban:  **Не забывайте** закрывать заявки. `[или Программисты... Ну вы поняли.. Они же модераторы..]`\n' +
                        ':ban:  **Если вы что-то забыли** то всегда есть **!помощь**. В ней кратко обо всём и ни о чём. `[вызывать справку можно только в канале` <#{0}>`]`\n\n'.format(self.config['requestsData']['channel']) +
                        '`P.s.` Если найдёте **ошибку в использовании бота**, немедля пишите <@290166276796448768>. Он почти в тот же день её исправит.  :EZY: \n' +
                        ':peepoCry: `- А теперь жамкайте на кирку и пора работать! Солнце ещё высоко!`\n:PepeHands:')
        await data['message'].channel.send(helpMsg, delete_after = 60)
        await data['message'].delete()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        newLog(exc_type, exc_obj, exc_tb, e)
