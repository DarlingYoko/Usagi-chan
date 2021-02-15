from src.functions import createEmbed, newLog, wrongMessage
import sys

async def helpValentine(self, data):
    try:
        if data['message'].channel.id != self.config['data'].getint('usualChannelId'):
            title = 'В этом канале нельзя использовать эту команду!'
            description = 'Вам сюда 👉 <#{0}>'.format(self.config['data']['usualChannelId'])
            await wrongMessage(data = data, title = title, description = description)
            await data['message'].delete()
            return

        title = 'Справка'
        description = '''> **Приветсвую вас на празднике всех влюбленных! Я - Купидон, помогу отправить вам валентинку!**

                            :round_pushpin: **Для создания валентинки** вам необходимо написать команду:
                            `!валентинка тип_отправителя/@Имя#тег/ваш поздравительный текст`
                            (Также вы можете прикрепить одну фотографию или гифку)

                            :round_pushpin:**Подсказочка** Для того чтобы получить правильный ник получателя, вам нужно ввести в поле ввода сообщения тег пользователя в любом канале на сервере и скопировать его.
                            :round_pushpin:**Пример никнейма**: `@Yoko#1234`
                            **АЛЁРТ!!!** Обязательно копируйте ник с сервера, тк нужен оригинальный ник пользователя, а не его серверный ник!!!

                            :round_pushpin:**Доступные типы валентинок**:
                                1) **"я"** - валентинка от вас без изменений
                                2) **"анон"** - валентинка от анона, тоже без изменений
                                3) **"что то на выбор из [Nuke73, Эмбер, Мона, Беннет, Паймон]"** - валентинка от этой личности, что то может поменятся))
                                4) **"рандом"** - валентинка от рандомной личности, произойти может всё что угодно! Как выдачи роли так и кое что ещё :pepoDetective:

                            :round_pushpin: **Пример создания**: `!валентинка рандом/@Usagi-chan#9716/Моя милая девочка, люблю тебя! <:loveKeqing:779460687218737162>`
                            Если в ответ вам ничего не пришло, значит вы как то неправильно указали **отправителя**

                            **ПРИМЕЧАНИЕ**: Все поля обязательно должны быть заполнены и разделены `/`'''
        thumbnail = ''
        embed = createEmbed(title = title, description = description, thumbnail = thumbnail)
        user = data['message'].author
        if not user.dm_channel:
            ch = await user.create_dm()
        else:
            ch = user.dm_channel

        await ch.send(embed = embed)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        newLog(exc_type, exc_obj, exc_tb, e)
