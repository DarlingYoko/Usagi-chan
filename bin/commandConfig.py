from string import Template


# 'command Name':{
#   'answer': 'some text',
#   'function': 'function()',
#   'delay': 5,
#}


commands = {
    'private': {
    },
    'guild':{
        'usual': {
            '!помощь':{
                'answer': '',
                'function': 'asyncio.run_coroutine_threadsafe(helpCommand(self, message), self.loop)',
                'delay': 1,
            },
            '!создать':{
                'answer': '',
                'function': 'asyncio.run_coroutine_threadsafe(createRequest(self, message, command), self.loop)',
                'delay': 1,
            },
            '!np':{
                'answer': 'self.musicPlayer.nowPlay()',
                'function': None,
                'delay': 5,
            },
            '!q':{
                'answer': 'self.musicPlayer.query()',
                'function': None,
                'delay': 60,
            },
            '!ч':{
                'answer': '',
                'function': 'asyncio.run_coroutine_threadsafe(boostPot(self, message), self.loop)',
                'delay': 1,
            },
            '!роль':{
                'answer': '',
                'function': 'asyncio.run_coroutine_threadsafe(createNewRole(self, message), self.loop)',
                'delay': None,
            },
            '!эмодзи':{
                'answer': '',
                'function': 'asyncio.run_coroutine_threadsafe(createNewEmoji(self, message), self.loop)',
                'delay': None,
            },
        },
        'music': {
            '!p':{
                'answer': 'Добавила песенку в плейлист',
                'function': 'self.musicPlayer.play(msg, command)',
                'delay': 5,
            },
            '!pause':{
                'answer': 'Поставила на паузу',
                'function': 'self.musicPlayer.pauseAudio()',
                'delay': 5,
            },
            '!r':{
                'answer': 'Поставила дальше играть',
                'function': 'self.musicPlayer.resume()',
                'delay': 5,
            },
            '!stop':{
                'answer': 'Остановила и очистила',
                'function': 'self.musicPlayer.stop()',
                'delay': 5,
            },
            '!shuffle':{
                'answer': 'Перемешала',
                'function': 'self.musicPlayer.shuffle()',
                'delay': 5,
            },
            '!s':{
                'answer': 'self.musicPlayer.skip()',
                'function': None,
                'delay': 5,
            },
            '!repeat':{
                'answer': 'self.musicPlayer.repeat(msg, command)',
                'function': None,
                'delay': 5,
            },
        },
        'token': {
            '!монета':{
                'answer': 'self.token.addToken(self, msg.split(command)[1].strip())',
                'function': None,
                'delay': 10,
            },
            '!немонета':{
                'answer': 'self.token.removeToken(self, msg.split(command)[1].strip())',
                'function': None,
                'delay': 5,
            },
            '!монеты':{
                'answer': 'self.token.viewToken(self)',
                'function': None,
                'delay': 60,
            },
        },
        'moviegoers':{
            '!удалить':{
                'answer': 'Удалила',
                'function': 'asyncio.run_coroutine_threadsafe(removeSession(self, msg), self.loop)',
                'delay': 5,
            },
        },
        'my':{
            '!connect':{
                'answer': 'Подключилась',
                'function': 'asyncio.run_coroutine_threadsafe(self.musicPlayer.connect(self.client, msg, command), self.loop)',
                'delay': 5,
            },
            '!remove':{
                'answer': 'Удалила и закрыла',
                'function': 'asyncio.run_coroutine_threadsafe(manualRemoveRequest(self, message, msg.split(command)[1].strip()), self.loop)',
                'delay': 5,
            },
        }

    }
}

texts = {
    'cock': '<:YEP:858375413360099360> COCK',
    'глоськ': '<:Huggu:832641068355813376>',
    'ёка': '<:pepoHappyHug:858271324928737280>',
    'йока': '<a:hack:835971234760097793>',
    'бава': '<a:ShiroHuggu:835966433262829668>',
    'гвин': '<:peepoHappy:858179418371784714>',
    'сили': '山匚Ɋ丨 乂丂 <a:02Heart:836051347652214784>',
    'айня': '<:peepoAweSome:829380320804601886>',
    'кешб': '<:peepoPolice:858179529699491861>',
    'трин': '<:Jebaited:827276677716770898>',
    'синг': '<a:peepoSadSwipe:858179554769895444>',
    'пепус': '<:lickDed:836220314118783046>',
    'яна': '<:peepoFlower:858146276604117033>',
    'яня': '<:peepoPANTIES:858179511447191582>',
    'саднёс': '<a:round:836226109191356427>',
    'саднес': '<a:round:836226109191356427>',
    'блади': '<a:borger:836047453186818079>',
    'хиджи': '<:kaban:858145849808781323>',
    'ивка': 'Нет блин Вика',
    'вика': 'Нет блин Ивка',
    'лисма': 'Нет блин Пукма',
    'пукма': 'Нет блин Лисма',
    'водинмекс': '<:EZY:858145758049075250>',
    'кеша': '<a:swing:836048490223108107>',
    'монополия': '<:diluc:836069264472670248>',
    'таката': 'Такаааааточка <:peepoAwesome:858146094394507324>',
    'рибаптика': '<a:peepoPats:858179518862458881>',
    'рыбапыца': '<a:peepoPats:858179518862458881>',
    'ангелок': ':cockroach:',
    'пискин': '<:pepeSmex:858251549007675422>',
    'никзип': '<:pepoHappyHug:858271324928737280> иди сюдаааа',
    'весдос': '<:peepoClown:858146169087328317>',
    'кегебе': '<a:cool:836240890204258364>',
    'фасег': '<:MonkaStop:837405113638977576>',
    'крейзи': '<:peepoBlanket:858146128021028894>',
    'голдас': '<:peepeSword:858146065069244447>',
    'траеры': '<a:solider:840549758581473290><a:solider:840549758581473290><a:solider:840549758581473290><a:solider:840549758581473290>',
    'скилфул': '<:peepoawesome:849713245640065074>',
    '!вебивент': '<:peepoawesome:849713245640065074>',
    '!форум': 'Ссылка на форум - https://www.hoyolab.com\nСсылка на логин бонус - https://webstatic-sea.mihoyo.com/ys/event/signin-sea/index.html?act_id=e202102251931481&lang=ru-ru',
    '!карта': 'Интерактивная карта по Геншину: https://webstatic-sea.mihoyo.com/app/ys-map-sea/?lang=ru-ru',
    '!хх': 'https://genshin.honeyhunterworld.com',
    '!hh': 'https://genshin.honeyhunterworld.com',
    '!паймон': 'https://paimon.moe/',
    'эр': '<:pepoVovan:858129919195217961>',
    'бананя': '<a:peepoTub:858754739968540702>',

}
#'': '',<::>
#сначала проверка на функцию, если функция есть, то ивал её, если нет, то ответ евал ансвера
