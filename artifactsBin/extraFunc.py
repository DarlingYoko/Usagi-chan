import re
from discord_components import Button, Select, ButtonStyle, InteractionType, SelectOption


def getTasks(self, check):
    resSelect = self.client.wait_for("select_option", check = check, timeout = 60.0)
    resBtn = self.client.wait_for("button_click", check = check, timeout = 60.0)
    tasks = [resSelect, resBtn]
    return tasks

















def getSets():
    sets = {
            'Архаичный камень': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982951932063784/Item_Flower_of_Creviced_Cliff.png',
                                    'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877982949751013426/Item_Feather_of_Jagged_Peaks.png',
                                    'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877982948115247134/Item_Sundial_of_Enduring_Jade.png',
                                    'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982953534259220/Item_Goblet_of_Chiseled_Crag.png',
                                    'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877982956524830770/Item_Mask_of_Solitude_Basalt.png',},

            'Заблудший в метели': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877984377303347290/Item_Snowswept_Memory.png',
                                    'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877984375675961415/Item_Icebreaker27s_Resolve.png',
                                    'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877984374174400602/Item_Frozen_Homeland27s_Demise.png',
                                    'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877984373301977139/Item_Frost-Weaved_Dignity.png',
                                    'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877984370550526032/Item_Broken_Rime27s_Echo.png',},

            'Рыцарь крови': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982786881998938/Item_Bloodstained_Flower_of_Iron.png',
                                'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877982780796063864/Item_Bloodstained_Black_Plume.png',
                                'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877982784948412436/Item_Bloodstained_Final_Hour.png',
                                'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982782545072178/Item_Bloodstained_Chevalier27s_Goblet.png',
                                'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877982788853334076/Item_Bloodstained_Iron_Mask.png',},

            'Горящая алая ведьма': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982356202471434/Item_Witch27s_Flower_of_Blaze.png',
                                    'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877982354449248376/Item_Witch27s_Ever-Burning_Plume.png',
                                    'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877982353144840242/Item_Witch27s_End_Time.png',
                                    'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982356831625246/Item_Witch27s_Heart_Flames.png',
                                    'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877982358593224814/Item_Witch27s_Scorching_Hat.png',},

            'Эмблема рассечённой судьбы': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877983787168976906/Item_Magnificent_Tsuba.png',
                                            'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877983794911666256/Item_Sundered_Feather.png',
                                            'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877983792931946577/Item_Storm_Cage.png',
                                            'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877983790943834172/Item_Scarlet_Vessel.png',
                                            'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877983789345804328/Item_Ornate_Kabuto.png',},

            'Конец гладиатора': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877981499062882314/Item_Gladiator27s_Nostalgia.png',
                                    'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877981485007769650/Item_Gladiator27s_Destiny.png',
                                    'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877981491349569536/Item_Gladiator27s_Longing.png',
                                    'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877981486517747782/Item_Gladiator27s_Intoxication.png',
                                    'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877981484122787950/Item_Gladiator27s_Triumphus.png',},

            'Сердце глубин': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877984345648951336/Item_Gilded_Corsage.png',
                                'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877984348261978173/Item_Gust_of_Nostalgia.png',
                                'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877984343673413713/Item_Copper_Compass.png',
                                'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877984346517176330/Item_Goblet_of_Thundering_Deep.png',
                                'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877984349595775016/Item_Wine-Stained_Tricorne.png',},

            'Ступающий по лаве': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982657634500628/Item_Lavawalker27s_Resolution.png',
                                    'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877982659261890590/Item_Lavawalker27s_Salvation.png',
                                    'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877982661291937822/Item_Lavawalker27s_Torment.png',
                                    'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982655759650856/Item_Lavawalker27s_Epiphany.png',
                                    'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877982662223085599/Item_Lavawalker27s_Wisdom.png',},

            'Возлюбленная юная дева': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982060747292723/Item_Maiden27s_Distant_Love.png',
                                        'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877982063863664710/Item_Maiden27s_Heart-stricken_Infatuation.png',
                                        'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877982059547725905/Item_Maiden27s_Passing_Youth.png',
                                        'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982063385513994/Item_Maiden27s_Fleeting_Leisure.png',
                                        'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877982065717542923/Item_Maiden27s_Fading_Beauty.png',},

            'Церемония древней знати': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982468769206332/Item_Royal_Flora.png',
                                        'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877982471923318834/Item_Royal_Plume.png',
                                        'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877982472850268210/Item_Royal_Pocket_Watch.png',
                                        'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982474582507540/Item_Royal_Silver_Urn.png',
                                        'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877982469914259477/Item_Royal_Masque.png',},

            'Бледный огонь': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877983995353251870/Item_Stainless_Bloom.png',
                                'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877983999111335936/Item_Wise_Doctor27s_Pinion.png',
                                'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877983993373528134/Item_Moment_of_Cessation.png',
                                'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877983997630750751/Item_Surpassing_Cup.png',
                                'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877983990651428915/Item_Mocking_Mask.png',},

            'Встречная комета': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877983490543616040/Item_Summer_Night27s_Bloom.png',
                                    'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877983491709616128/Item_Summer_Night27s_Finale.png',
                                    'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877983495459319918/Item_Summer_Night27s_Moment.png',
                                    'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877983496679862312/Item_Summer_Night27s_Waterballoon.png',
                                    'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877983493550923846/Item_Summer_Night27s_Mask.png',},

            'Воспоминания Симэнавы': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877983658273804319/Item_Entangling_Bloom.png',
                                        'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877983661776048140/Item_Shaft_of_Remembrance.png',
                                        'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877983660379349052/Item_Morning_Dew27s_Moment.png',
                                        'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877983659045576744/Item_Hopeful_Heart.png',
                                        'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877983656315084850/Item_Capricious_Visage.png',},

            'Стойкость Миллелита': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877984131294851092/Item_Flower_of_Accolades.png',
                                    'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877984129793282098/Item_Ceremonial_War-Plume.png',
                                    'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877984136063746119/Item_Orichalceous_Time-Dial.png',
                                    'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877984134176342036/Item_Noble27s_Pledging_Vessel.png',
                                    'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877984132725096519/Item_General27s_Ancient_Helm.png',},

            'Громогласный рёв ярости': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877981917050441768/Item_Thunderbird27s_Mercy.png',
                                        'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877981908728938577/Item_Survivor_of_Catastrophe.png',
                                        'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877981906719883284/Item_Hourglass_of_Thunder.png',
                                        'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877981907168673802/Item_Omen_of_Thunderstorm.png',
                                        'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877981909920141312/Item_Thunder_Summoner27s_Crown.png',},

            'Усмиряющий гром': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877981771860410379/Item_Thundersoother27s_Heart.png',
                                'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877981772707688459/Item_Thundersoother27s_Plume.png',
                                'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877981767754211328/Item_Hour_of_Soothing_Thunder.png',
                                'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877981769972985917/Item_Thundersoother27s_Goblet.png',
                                'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877981768685330482/Item_Thundersoother27s_Diadem.png',},

            'Изумрудная тень': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982200488923156/Item_In_Remembrance_of_Viridescent_Fields.png',
                                'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877982200769970226/Item_Viridescent_Arrow_Feather.png',
                                'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877982202829365329/Item_Viridescent_Venerer27s_Determination.png',
                                'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877982208521039882/Item_Viridescent_Venerer27s_Vessel.png',
                                'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877982203471089674/Item_Viridescent_Venerer27s_Diadem.png',},

            'Странствующий ансамбль': {'цветок': 'https://cdn.discordapp.com/attachments/877981304644304926/877981623554035762/Item_Troupe27s_Dawnlight.png',
                                        'перо': 'https://cdn.discordapp.com/attachments/877981304644304926/877981620089528390/Item_Bard27s_Arrow_Feather.png',
                                        'часы': 'https://cdn.discordapp.com/attachments/877981304644304926/877981621393965106/Item_Concert27s_Final_Hour.png',
                                        'кубок': 'https://cdn.discordapp.com/attachments/877981304644304926/877981625554706472/Item_Wanderer27s_String_Kettle.png',
                                        'шапка': 'https://cdn.discordapp.com/attachments/877981304644304926/877981622044065842/Item_Conductor27s_Top_Hat.png',},
            }

    return sets



def listCheckEntry(entry, list):
    for i in list:
        if i in entry:
            return True

    return False


def getNumberByLVL(base, extra, lvl):
    wrongLvls = [4, 10, 17]
    #на 4 10 17 + 204 вместо 203
    add = 0
    for i in wrongLvls:
        if lvl >= i:
            add += 1
    count = base + extra * lvl + add

    return str(count)

def numDecimalPlaces(value):
    m = re.match(r"^[0-9]*\.([0-9]([0-9]*[1-9])?)0*$", value)
    return len(m.group(1)) if m is not None else 0


def getStats():
    allStats = {'ATK': {16: 258, 20: 311, 'max': 114},
                'ATK%': {'max': 34.8},
                'CRIT DMG': {16: 51.6, 20: 62.2, 'max': 46.7},
                'CRIT RATE': {16: 25.8, 20: 31.1, 'max': 23.3},
                'HP': {16: 3967, 20: 4780, 'max': 1794},
                'HP%': {'max': 34.8},
                'HEAL BONUS': {16: 29.8, 20: 35.9},
                'DEF': {'max': 138},
                'DEF%': {16: 48.4, 20: 58.3, 'max': 43.7},
                'EM': {16: 155, 20: 187, 'max': 138},
                'ER': {16: 38.7, 20: 51.8, 'max': 39},
                'elements': {16: 38.7, 20: 46.6,},
                'PHYSICAL DMG': {16: 48.4, 20: 58.3,},}

    elements = ['ANEMO', 'HYDRO', 'GEO', 'PYRO', 'CRYO', 'ELECTRO', 'ATK%', 'HP%']

    mainStats = {'цветок': ['HP'],
                'перо': ['ATK'],
                'часы': ['HP%', 'DEF%', 'ATK%', 'ER', 'EM'],
                'кубок': ['HP%', 'DEF%', 'ATK%', 'EM', 'ANEMO DMG', 'PHYSICAL DMG',
                            'HYDRO DMG', 'GEO DMG', 'PYRO DMG', 'CRYO DMG', 'ELECTRO DMG'],
                'шапка': ['HP%', 'DEF%', 'ATK%', 'EM', 'CRIT DMG', 'CRIT RATE', 'HEAL BONUS'],}

    return allStats, elements, mainStats


def getQueryBtns(self, page):
    emojiStart = self.client.get_emoji(873921151896805487)
    emojiPrevious = self.client.get_emoji(873921151372513312)
    emojiNext = self.client.get_emoji(873921151716438016)
    emojiEnd = self.client.get_emoji(873921151280234537)
    btnStart = Button(style=ButtonStyle.gray, emoji = emojiStart, id = 'start')
    btnPrevious = Button(style=ButtonStyle.gray, emoji = emojiPrevious, id = 'previuos')
    btnNext = Button(style=ButtonStyle.gray, emoji = emojiNext, id = 'next')
    btnEnd = Button(style=ButtonStyle.gray, emoji = emojiEnd, id = 'end')
    page = Button(style=ButtonStyle.gray, label = page, id = 'page', disabled = True)
    components=[[btnStart, btnPrevious, page, btnNext, btnEnd,]]
    return components
