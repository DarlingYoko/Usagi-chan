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
                'answer': 'Готово',
                'function': 'asyncio.run_coroutine_threadsafe(helpCommand(self, message), self.loop)',
                'delay': 1,
            },
            '!создать':{
                'answer': 'Готово',
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
                'answer': 'self.musicPlayer.repeat(msg)',
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
        }

    }
}

texts = {
    'cock': '<:YEP:771044606913151002> COCK',
    'глоськ': '<:Huggu:832641068355813376>',
    'ёка': '<:pepoHappyHug:832270928830136381>',
    'йока': '<a:hack:835971234760097793>',
    'бава': '<a:ShiroHuggu:835966433262829668>',
    'гвин': '<:peepoHappy:785159818901192704>',
    'сили': '山匚Ɋ丨 乂丂 <a:02Heart:836051347652214784>',
    'айня': '<:peepoAweSome:829380320804601886>',
    'кешб': '<:peepoPolice:811433053221027861>',
    'трин': '<:Jebaited:827276677716770898>',
    'синг': '<a:peepoSadSwipe:812443076542464050>',
    'пепус': '<:peepoFat:804710814275207213>',
    'яна': '<:peepoFlower:818264472282988564>',
    'яня': '<:peepoPANTIES:794786607877718047>',
    'саднесас': '<a:Agakakskagesh:771063271973060608>',
    'блади': '<a:borger:836047453186818079>',
    'хиджи': '<:kaban:802117569296203796>',
    'ивка': 'Нет блин Вика',
    'вика': 'Нет блин Ивка',
    'лисма': 'Пукма',
    'вимекс': '<:EZY:771041695671648329>',
    'кеша': '<a:swing:836048490223108107>',
    'монополия': '<:diluc:836069264472670248>',
    'таката': 'Такаааааточка <:peepoAwesome:810215328780910612>',
    'рибаптика': '<a:peepoPats:782171072748716032>',
    'рыбапыца': '<a:peepoPats:782171072748716032>',
    'онли': '<:peepoRot:779837278213505036>',
    'ангелкок': ':cockroach:',
    'фатсуня': '<:HuTaoHeart:825010377355034646>',
    'пискин': '<:pepeSmex:830749504235634728>',
    'никзип': '<:pepoHappyHug:832270928830136381> иди сюдаааа',
    #'': '',

}
#'': '',<::>
#сначала проверка на функцию, если функция есть, то ивал её, если нет, то ответ евал ансвера
