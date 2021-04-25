
import shelve, discord, random, asyncio
from src.functions import createEmbed
from time import sleep
from threading import Thread
from datetime import datetime, timedelta
from discord.utils import get

def getType(input):
    if input == 'я':
        return 1
    elif input == 'анон':
        return 2
    return input.lower()


def WeightedPick(ls):
    m, n = 0, random.uniform(0, sum([x for x in ls.values()]))
    for item, weight in ls.items():
        if n > m and n <= m+weight:
            return item
        m += weight


def userRole(roles, roleId):
    for role in roles:
        if roleId == role.id:
            return 1

    return 0

async def waitBan(loop, time, user, banRole):
    sleep(time)
    asyncio.run_coroutine_threadsafe(removeTimeRole(user, banRole), loop)

async def removeTimeRole(user, banRole):
    await user.remove_roles(banRole)

async def ban(self, guild, userId1, userId2, time):
    banRoleId = 799419044108566568
    banRole = discord.utils.get(guild.roles, id = banRoleId)
    try:
        user1 = await guild.fetch_member(userId1)
        user2 = await guild.fetch_member(userId2)
    except discord.errors.NotFound:
        return 0

    if not userRole(user1.roles, banRoleId):
        await user1.add_roles(banRole)
        Thread(target=asyncio.run, args=(waitBan(self.loop, time, user1, banRole), )).start()

    if not userRole(user2.roles, banRoleId):
        await user2.add_roles(banRole)
        Thread(target=asyncio.run, args=(waitBan(self.loop, time, user2, banRole), )).start()

    return 1


async def addRole(guild, userId, roleId):
    role = discord.utils.get(guild.roles, id = roleId)
    try:
        user = await guild.fetch_member(userId)
    except discord.errors.NotFound:
        return 0

    if not userRole(user.roles, roleId):
        await user.add_roles(role)
        return 1

    return -1

async def removeRole(guild, userId, roleId):
    role = discord.utils.get(guild.roles, id = roleId)
    try:
        user = await guild.fetch_member(userId)
    except discord.errors.NotFound:
        return 0

    if userRole(user.roles, roleId):
        await user.remove_roles(role)
        return 1


    return -1

async def banUsual(self, guild, usualChannel):

    role = get(guild.roles, id = 346775939105161247)
    permissions = usualChannel.overwrites_for(role)
    permissions.send_messages = False
    await usualChannel.set_permissions(role, overwrite = permissions)
    Thread(target=asyncio.run, args=(waitRasban(self.loop, role, usualChannel), )).start()


async def waitRasban(loop, role, usualChannel):
    sleep(1 * 60)
    asyncio.run_coroutine_threadsafe(rasban(role, usualChannel), loop)

async def rasban(role, usualChannel):
    permissions = usualChannel.overwrites_for(role)
    permissions.send_messages = True
    await usualChannel.set_permissions(role, overwrite = permissions)
    await usualChannel.send('Урааа свобода!!')


async def valentineCommand(self, data):

    guild = await self.client.fetch_guild(self.config['data']['guildId'])
    messageChannel = await self.client.fetch_channel(self.config['valentineData']['messageChannel'])
    usualChannel = await self.client.fetch_channel(self.config['data']['usualChannelId'])
    logChannel = await self.client.fetch_channel(self.config['valentineData']['logChannel'])


    await data['message'].channel.send('А всё! Ивент закончился, спасибо что учавствовали! <3')
    return

    #if datetime.now() - self.members.getMember(data['message'].author.id)['lastMsg'] < timedelta(minutes = 1):
        #await data['message'].channel.send('Слишком рано для новой командой, подождите 1 min')
        #return


    guild = await self.client.fetch_guild(self.config['data']['guildId'])
    banChannel = await self.client.fetch_channel(self.config['valentineData']['banChannel'])



    fischlTexts = ['Я - Фишль, Принцесса осуждения, волею судьбы призванная в этот мир... Что? Ты тоже путешественник из другого мира? Что ж, хорошо, Я милостиво позволю тебе путешествовать со мной.',
                   'Звёзды на чёрном бархате небосвода - не что иное, как зияющие дыры, что выклёвывает Оз в его ткани под покровом бесконечной ночи.',
                   'Мы будем глубоким и безмятежным твой сон, и пусть минуют тебя кошмары. В конце концов, разве смеют они посещать тех, кто благословлен Нирваной Ночи?',
                   'Я, хозяйка Нирваны Ночи, принцесса осуждения, призываю тебя быть готовым защищать путешественника от превратностей его судьбы и, в случае необходимости, отдать жизнь за то, чтобы вырвать его из лап всепоглощающей тьмы!',
                   'Хм, прекрасный вид. Это напоминает мне о пейзажах в моём мире, где кровь и слёзы грешников застыли перед лицом Принцессы Осуждения',
                   'Еда - это лишь оковы для смертного тела. Но если ты очень хочешь услышать ответ, вот он: нет более достойной пищи для принцессы осуждения, чем слёзы грешников и языки лжецов...']


    kisikTexts = ['''Люблю свою вайфу, вот вы говорите, тянки не нужна, моя вайфу лучше, мой хасбэнд лучше, но я то знаю что моя будет лучше вашей по следующим причинам. Как то утром моя вайфу (не буду говорить кто это что бы вы не обижались) приготовила мне тофу, такое сладкое, ещё она с помощью соуса написала моё имя, я таким был счастливым и конечно запостил это на свой форму в Михойо, но мне написала бывшая вайфу и у них началась война, а там ещё и вайфу детства подтянулась но суть не в этом. В итоге, ребята, любите свою вайфу, даже если у вас есть свой гарем''',
                  '''Однажды утром я прохожу мимо магазина баннеров и просматриваю появился ли там мой баннер с моей вайфу. Я каждый перепроверяю и захожу лично спрашивать, есть ли там моя Ху Тао, Аяка, Розария, Синьора но этот гнусный продавец все так же отвергает и безэмоционально вертит головой но я это знаю что он где то припрятал моих вайфу. Каждый день  у нас эта игра продолжается, из за дня в день, я уже чувствую что у нас появилась вербальная связь. Я бросаю на него свой взгляд и он всё так же кивает головой, так происходит уже пол года но когда нибудь я доберусь до своей Вайфу.''',
                  '''Я обычный персонаж геншина который идёт в свой дом и кушает дома свои любимый оладушки приготовленной моей вайфу/хасбэндом. Каждый вечер я сижу за своим камином, слушаю классическую музыку, пью ромашковый чай, выгуливаю собаку и укладываюсь спать. Новое утро, новый день, я встречаю с шоколадкой которую подаёт мне моя вайфу, я люблю её а она меня. Любите своих лапуличек''']

    msg = data['content'].split('/')
    if len(msg) < 3 or len(msg) > 3:
        title = 'Неправильный формат валентинки. Прочтите синтаксис!'
        description = '''
        :round_pushpin: Использование: `!валентинка <от кого>/<кому>/<сообщение>`
        :round_pushpin: Пример: `!валентинка я/@Raiva#7811/Люблю Райву!!`
        **ПРИМЕЧАНИЕ**: Все поля обязательно должны быть заполнены и разделены `/`'''
        embed = createEmbed(title = title, description = description)
        await data['message'].channel.send(embed = embed)
        return


    type = getType(msg[0].strip())
    user = msg[1][1:].split('#')
    if len(user) != 2:
        title = 'Неверное введено имя получателя валентинки!'
        description = 'Имя должно быть в формате @`Имя`#`тег`'
        embed = createEmbed(title = title, description = description)
        await data['message'].channel.send(embed = embed)
        return

    name = user[0]
    tag = user[1]
    forUser = self.members.findByName(name, tag)
    content = msg[2]
    # проверка на себя
    if data['message'].author.id == forUser:
        await data['message'].channel.send('Низя отправлять валентнику самому себе :PepeMAD:')
        return

    if not forUser:
        await data['message'].channel.send('Пользователь не найден')
        return

    answer = ''
    title = '{0} создаёт новую заявку.'.format(data['message'].author.display_name)
    authorIconURL = data['message'].author.avatar_url
    thumbnail = self.config['valentineData']['thumbnail']
    file = ''

    if type == 1:
        title = 'Валентинка от {0}.'.format(data['message'].author.display_name)
        answer ='Не анонимная валентинка, успешно отправлена!'

    if type == 2:
        title = 'Анонимная валентинка!'
        answer = 'Анонимная валентинка, успешно отправлена!'
        authorIconURL = ''


    accessDict = ['нюк', 'эмбер', 'беннет', 'паймон', 'мона']
    if type in accessDict:
        if type == 'нюк':
            title = 'Валентинка от Нюка!'
            answer = 'Вы успешно отправили валентинку от Нюка!'
            data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/810268111546089472/unknown.png'

        if type == 'эмбер':
            title = 'Валентинка от Эмбер!'
            answer = 'Вы успешно отправили валентинку от Эмбер!'
            content = 'О БОЖЕ БОЖЕ БОЖЕ, МЕНЯ НАКОНЕЦ-ТО ВЫБРАЛИ В КАЧЕСТВЕ ПОСЫЛЬНОГО!! \nЯ безумна счастлива, спасибо тому кто выбрал меня <3. \nА тебе, дорогой получатель, передаю частичку своей радости и счастья. Пусть у тебя все будет хорошо в этот воскресный день! Цмоки!'
            data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/809824879644901396/ember.png'

        if type == 'беннет':
            title = 'О нет! Беннет всё перепутал и отправил валентинку не от себя, а от {0}.'.format(data['message'].author.display_name)
            answer = 'О нет! Беннет всё перепутал и отправил валентинку не от себя, а от вас!'

        if type == 'паймон':
            title = 'Валентинка от Паймон!'
            answer = 'Вы успешно отправили валентинку от Паймон!'
            thumbnail = 'https://i.ibb.co/wyXSzxr/6.png'

        if type == 'мона':
            title = 'Валентинка от Моны!'
            answer = 'Вы успешно отправили валентинку от Моны!'
            thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/810152431044395028/monaheart.png'

        authorIconURL = ''



    randomDict = {'кокчурл': 150, 'чиф': 75, 'райва': 30, 'конеко': 75, 'екатерина': 150, 'аяка': 150,
                  'барбара': 150, 'тимми': 150, 'тухед': 125, '5хед': 150, 'альбедо': 150, 'криочурл': 150,
                  'диона': 150, 'дилюк': 150, 'кринжик': 150, 'кли': 150,
                  'джинн': 150, 'лиза': 150, 'фишль': 150, 'повар': 10, 'топ': 450}



    if type == 'рандом':
        type = WeightedPick(randomDict)
        if type == 'кокчурл':
            title = 'Валентинка от Кокчурла!'
            answer = 'Хехе, Вам выпал Кокчурл, я более чем уверен, что получатель очень обрадуется :pepeChill:'
            data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/810138220615827496/cock.png'

        if type == 'чиф':
            title = 'Валентинка от 4iiif!'
            answer = 'Вы успешно отправили валентинку от ЧИИИИИИИИФ!'
            content = ''
            data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/810144800220512296/ban.png'
            if not await ban(self, guild, data['message'].author.id, forUser, 60):
                await data['message'].channel.send('Не верно указан пользователь, также проверьте, присутствует ли он на сервере.')
                return
            banPhoto = discord.File('files/photo/ban.jpeg')
            await banChannel.send('<@{0}> <@{1}>\nБери стул и присаживайся :peepoDown:\n\nОтдыхайте 1 мин'.format(data['message'].author.id, forUser), file = banPhoto)


        if type == 'райва':
            title = ''
            answer = 'Ахуеть вам выпал Райва!'

            file = discord.File('files/gif/2.gif') #Жебер поднимает голову из кокаина
            await data['message'].channel.send(answer)
            await logChannel.send('Валентинка от Райвы, кек, \n<@{0}>'.format(data['message'].author.id))
            await messageChannel.send('О нет, на сервере что-то пошло не так и <@{0}> попал своей валентинкой в Райву... :MonkaChrist:'.format(data['message'].author.id), file = file)
            await banUsual(self, guild, usualChannel)
            await usualChannel.send('**ЛОЖИСЬ, КТО ТО ПОТРЕВОЖИЛ РАЙВУ!!!**\n\n\nhttps://youtu.be/iICQ3w6p0jk')
            await usualChannel.send('Можете пока покекать с валентинок в <#{0}>'.format(self.config['valentineData']['messageChannel']))



        if type == 'конеко':
            title = 'Валентиночка от Конеко-чан!'
            content = '*Бам* по голове волшебным банхаммером, Ня!'
            data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/810224161511178250/unknown.png'
            thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/810224869644042260/file_8031353.png'
            answer = 'Вам выпала самая милая неко-тян Конеко, Ня!'
            if not await ban(self, guild, data['message'].author.id, forUser, 60):
                await data['message'].channel.send('Не верно указан пользователь, также проверьте, присутствует ли он на сервере.')
                return
            banPhoto = discord.File('files/photo/ban.jpeg')
            await banChannel.send('<@{0}> <@{1}>\nБери стул и присаживайся :peepoDown:\n\nОтдыхайте 1 мин'.format(data['message'].author.id, forUser), file = banPhoto)

        if type == 'екатерина':
            title = 'Валентинка от Екатерины!'
            content = 'Приветсвую тебя, путешествинник!\nМне нужна твоя помощь в новом задании, и поэтому я награждаю тебя ролью <@&810229945321521183>, чтобы ты мог успешно выполнить моё поручение.'
            answer = 'Вам выпала известный агрегатор квестов Екатерина!'
            if not await addRole(guild, forUser, 810229945321521183):
                await data['message'].channel.send('Не верно указан пользователь, также проверьте, присутствует ли он на сервере.')
                return


        if type == 'аяка':
            title = 'Валентинка от Аяки, хоть у кого то она будет)!'
            answer = 'Поггерс Аяка и вправду существует)!'
            thumbnail = 'https://i.ibb.co/jJPJ1Hv/ayaka-2.jpg'

        if type == 'барбара':
            title = 'Валентинка от Барбары. ИКУЁ!!'
            answer = 'Вы успешно отправили валентинку от Барбары. ИКУЁ!!!'
            thumbnail = 'https://i.ibb.co/9rh63XQ/GENSHIN-IMPACT-BARBARA.jpg'
            file = discord.File('files/audio/{0}.mp3'.format(random.randint(1,4)))


        if type == 'тимми':
            title = 'Валентинка от Тимми, будте аккуратнее при фарме голубей!'
            answer = 'Вам выпал очень милый и тихий мальчик Тимми, но будте аккуратнее при фарме голубей!!'
            data['urlImage'] = 'https://i.ibb.co/dkKt5sz/1500449504199166887.jpg'

        if type == 'тухед':
            title = 'Валентинка от Тухеда!'
            content += content + ':2Head: '
            answer = 'Ну ты и Глууупик :2Head:'
            thumbnail = 'https://cdn.discordapp.com/emojis/771044700630548520.png?v=1'
            if not await addRole(guild, forUser, 810229339664678922):
                await data['message'].channel.send('Не верно указан пользователь, также проверьте, присутствует ли он на сервере.')
                return
            await usualChannel.send('<@{0}>\nVasiliy551 благословил и наградил ролью Глупик вас! Ну не вас, а <@{1}>! :2Head:'.format(data['message'].author.id, forUser))

        if type == '5хед':
            title = 'Валентинка от 5Хеда!'
            answer = 'Самый умный чтоли? :5Head::monkaMEGA:'
            thumbnail = 'https://cdn.discordapp.com/emojis/771045005691060224.png?v=1'
            res = await removeRole(guild, forUser, 810229339664678922)
            if res == 0:
                await data['message'].channel.send('Не верно указан пользователь, также проверьте, присутствует ли он на сервере.')
                return

            if res == 1:
                await usualChannel.send('**Важное объявление!!**\n<@{0}> был замечен в компании :5Head:. Командир Vasiliy551 принимает решение изгнать <@{0}> из своих рядов.'.format(forUser))

        if type == 'альбедо':
            title = 'Валентинка от Альбедо!'
            answer = 'Вы успешно отправили валентинку от Альбедо!'
            if not await addRole(guild, forUser, 810228843477991444):
                await data['message'].channel.send('Не верно указан пользователь, также проверьте, присутствует ли он на сервере.')
                return

        if type == 'криочурл':
            title = 'Валентинка от Павшего Криочурла! Молодец, стремись к новым победам!'
            answer = 'Вы успешно отправили валентинку от Павшего Криочурла!'
            data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/810175264934854686/krio.png'

        if type == 'диона':
            title = 'Валентинка от Дионы!'
            answer = 'Вы успешно отправили валентинку от Дионы!'
            content = 'У меня самый **НЯШНЫЙ ФОН!!!**\n' + content
            thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/810176761581142016/799559636474658846.png'

        if type == 'дилюк':
            title = 'Валентинка от Полуночного шахтёра!'
            answer = 'Вы успешно отправили валентинку от Дилюка! Не забудь собрать руду!'
            data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/810179924832550972/diluc.png'
            thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/810180279216898098/diluc_1.png'

        if type == 'кринжик':
            title = 'Валентинка от Сёкисика, получите дополнительное описание к валентинке!'
            content += ('\n\n' + random.choice(kisikTexts))
            answer = 'Вы успешно отправили валентинку от Сёкисика!'
            thumbnail = 'https://cdn.discordapp.com/avatars/303086616912855041/1d9a1e24e6e7f3df08825fe0774ac021.png?size=4096'

        if type == 'кли':
            title = 'Валентинка от Кли! БУм БУм Бакудан.'
            answer = 'Вы успешно отправили валентинку от Кли!'
            content = 'Перед тем как передать вам валентинку, Кли решилась прогулятся по окрестностям Мондштата, но настолько увлеклась, что потеряла ваше послание. Поэтому Кли, в наказание передаёт вам все свои заготовленные бомбы.'
            thumbnail = 'https://cdn.discordapp.com/attachments/802669608711618600/809837039536701500/klee_trip.png'
            data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/810194898882920467/ezgif.com-gif-maker.gif'


        if type == 'джинн':
            title = 'Валентинка от Джинн! Вауу, вот это удача))))'
            answer = 'Вы успешно отправили валентинку от Джин!'
            content += '\n\nhttps://clips.twitch.tv/OpenOutstandingHeronNerfBlueBlaster'
            thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/810197467093139496/jean.png'

        if type == 'лиза':
            title = 'Валентинка от Лизы!'
            answer = 'Вы успешно отправили валентинку от Лизы!'
            file = discord.File('files/audio/5.mp3')

        if type == 'фишль':
            title = 'Валентинка от Принцессы осуждения!'
            answer = 'Вы успешно отправили валентинку от Принцессы осуждения!'
            content = random.choice(fischlTexts)
            thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/810199171687514143/Fischl-full-3126223.jpg'
            data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/810199188113588314/Fischle1.png'

        if type == 'повар':
            title = 'Валентинка от Intel_power!'
            answer = 'Вы успешно отправили валентинку от Intel_power!'
            content = 'ПОООГ ВАМ ВЫПАЛА ЛЕГЕНДАРКА! :peepoFat:'
            res = await addRole(guild, forUser, 810230331855994890)
            if res == 0:
                await data['message'].channel.send('Не верно указан пользователь, также проверьте, присутствует ли он на сервере.')
                return

            if res == 1:
                await usualChannel.send('**Важное объявление!!**\n<@{0}> выиграл АААААААВТОМОБИИИИИИИИЛЬ, конечно же нет :PepeHands: Но на ближайший месяц вы становитесь самым уважаемым пользователем нашего любииииимого дискорда. Наслаждайтесь! :loveKeqing: Теперь вы можете соединять сердца одиночек :YEP:'.format(forUser))

        if type == 'топ':
            title = 'Валентинка от одной из топа вайфу!'
            res = random.randint(1,3)
            if res == 1:
                title = 'Валентинка от Мисс Декабрь!'
                thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/810205203785711616/monatriumphant.png'
                data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/810205312569180180/unknown.png'
            if res == 2:
                title = 'Валентинка от Мисс Январь!'
                thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/810205566378835968/unknown.png'
                data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/810205643558354984/unknown.png'
            if res == 3:
                title = 'Валентинка от Мисс Февраль!'
                thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/810205679293825086/unknown.png'
                data['urlImage'] = 'https://cdn.discordapp.com/attachments/801159693404864543/810206384615981066/unknown.png'

            answer = 'Вы успешно отправили валентинку от одной из топа вайфу!'


        authorIconURL = ''

    if answer and title:
        embedLog = createEmbed(authorName = title, authorIconURL = authorIconURL,
                               description = '**Пользователь** - <@{0}>\nДля пользователя - <@{3}>\n**Сообщение** - {1}\n**Тип** - {2}\n'.format(data['message'].author.id, content, type, forUser),
                               color = 0x00ff00,
                               urlImage = data['urlImage'])

        embedMes = createEmbed(authorName = title, authorIconURL = authorIconURL,
                               description = '{0}\n'.format(content),
                               color = 0x00ff00,
                               urlImage = data['urlImage'],
                               thumbnail = thumbnail)
        await logChannel.send(embed=embedLog)
        await messageChannel.send('<@{0}>'.format(forUser), embed=embedMes)
        if file:
            await messageChannel.send(file = file)
        await data['message'].channel.send(answer)

        self.members.dict[data['message'].author.id]['lastMsg'] = datetime.now()
