import re
from discord_components import Button, Select, ButtonStyle, SelectOption
from discord import File


def get_tasks(ctx, check):
    resSelect = ctx.bot.wait_for("select_option", check = check, timeout = 60.0)
    resBtn = ctx.bot.wait_for("button_click", check = check, timeout = 60.0)
    tasks = [resSelect, resBtn]
    return tasks




def get_sets():
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



def list_check_entry(entry, list):
    for i in list:
        if i in entry:
            return True

    return False


def num_decimal_places(value):
    m = re.match(r"^[0-9]*\.([0-9]([0-9]*[1-9])?)0*$", value)
    return len(m.group(1)) if m is not None else 0


def get_stats():
    allStats = {'ATK': {16: 258, 20: 311, 'max': 114},
                'ATK%': {'max': 34.8},
                'CRIT DMG': {16: 51.6, 20: 62.2, 'max': 46.7},
                'CRIT RATE': {16: 25.8, 20: 31.1, 'max': 23.3},
                'HP': {16: 3967, 20: '4 780', 'max': 1794},
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



def generate_text(main = None, subs = [None, None, None, None]):
        result = []
        percent = ['CRIT', '%', 'DMG', 'BONUS', 'ER']

        if main:
            state = main.copy()
            state[1] = str(state[1])
            if list_check_entry(state[0], percent):
                state[1] += '%'
            res = '`{0}{1}{2}{3}{4}`'.format(state[0], ' '*(13-len(state[0])), '—', ' '*(13-len(state[1])), state[1])
        else:
            res = '`—{}—`'.format(' '*25)
        result.append({'name': res, 'value': '_ _', 'inline': False})
        result.append({'name': '┏━━━━━━━━━━━┓', 'value': '_ _', 'inline': False})

        for sub in subs:

            if sub:
                state = sub.copy()
                state[1] = str(state[1])
                if list_check_entry(state[0], percent):
                    state[1] += '%'
                res = '`{0}{1}{2}{3}{4}`'.format(state[0], ' '*(13-len(state[0])), '—', ' '*(13-len(state[1])), state[1])
            else:
                res = '`—{}—`'.format(' '*25)
            result.append({'name': res, 'value': '_ _', 'inline': False})


        result.append({'name': '┗━━━━━━━━━━━┛', 'value': '_ _', 'inline': False})
        return result

def get_components(label, list):
    components=[
                Select(
                    placeholder=label,
                    options=[SelectOption(label=item, value=item) for item in list],
                    custom_id="select",
                    ),
                ]
    return components

def get_buttons(ctx, zero = True, dot = True):
    btn1 = Button(style=ButtonStyle.gray, label = '1', id = '1')
    btn2 = Button(style=ButtonStyle.gray, label = '2', id = '2')
    btn3 = Button(style=ButtonStyle.gray, label = '3', id = '3')
    btn4 = Button(style=ButtonStyle.gray, label = '4', id = '4')
    btn5 = Button(style=ButtonStyle.gray, label = '5', id = '5')
    btn6 = Button(style=ButtonStyle.gray, label = '6', id = '6')
    btn7 = Button(style=ButtonStyle.gray, label = '7', id = '7')
    btn8 = Button(style=ButtonStyle.gray, label = '8', id = '8')
    btn9 = Button(style=ButtonStyle.gray, label = '9', id = '9')
    btn0 = Button(style=ButtonStyle.gray, label = '0', id = '0', disabled = zero)
    btnDot = Button(style=ButtonStyle.gray, label = '.', id = '.', disabled = dot)

    btnInvisible = Button(style=ButtonStyle.gray, label = '-', disabled = True)


    emojiAccept = ctx.bot.get_emoji(874767321007276143)
    emojiExit = ctx.bot.get_emoji(874767320915005471)


    btnClear = Button(style=ButtonStyle.gray, label = 'C', id = 'clear')
    btnAccept = Button(style=ButtonStyle.green, emoji = emojiAccept, id = 'accept')
    btnCleanEntry = Button(style=ButtonStyle.gray, label = 'CE', id = 'clean entry')
    btnExit = Button(style=ButtonStyle.red, emoji = emojiExit, id = 'exit')

    components=[[btn1, btn2, btn3, btnClear], [btn4, btn5, btn6, btnCleanEntry], [btn7, btn8, btn9, btnAccept], [btnInvisible, btn0, btnDot, btnExit], ]

    return components


async def quit(ctx, question):
    print('Exit')
    components=[]
    await question.edit(components = components)
    await question.delete(delay = 10)
    await ctx.message.delete(delay = 10)


def put_artifact_in_database(db, user, artifact):
    request = f"INSERT INTO artifacts VALUES(DEFAULT, \'{artifact.set}\', \'{artifact.part}\', {artifact.lvl}, \'{artifact.main[0]}\', \'{artifact.main[1]}\'"
    #request = f"INSERT INTO artifacts VALUES(DEFAULT, \'{artifact}\'"

    for sub in artifact.subs:
        request += f", \'{sub[0]}\', \'{sub[1]}\'"

    request += f",\'{artifact.part_url}\',\'{artifact.gs}\') RETURNING id;"
    respond_put_artifact = db.custom_command(request)

    if respond_put_artifact != 0:
        artifact_id = respond_put_artifact[0][0]
        user_artifacts = db.get_value(tableName = 'users_arts', argument = 'artifacts', selector = 'user_id', value = user.id)

        if user_artifacts:
            user_artifacts = eval(user_artifacts)
            user_artifacts.append(artifact_id)
            respond = db.update(tableName = 'users_arts', argument = 'artifacts', selector = 'user_id', newValue = str(user_artifacts), findValue = user.id)

        else:
            artifactsIDs = [artifact_id]
            respond = db.insert('users_arts', user.id, str(artifactsIDs))

        if respond:
            return artifact_id

    return 0


class Artifact:
    def __init__(self, set = None, part = None, lvl = None, main = None, subs = [None, None, None, None], id = None):
        self.set = set
        self.part = part
        self.lvl = lvl
        self.main = main
        self.subs = subs
        self.id = id

    def rate(self):
        weights = {'HP': 0, 'ATK': 0.5, 'ATK%': 1, 'ER': 0.5, 'EM': 0.5,
        			   'PHYSICAL DMG': 1, 'CRIT RATE': 1, 'CRIT DMG': 1, 'ELEM': 1,
        			   'HP%': 0, 'DEF%': 0, 'DEF': 0, 'HEAL BONUS': 0}


        max_mains = {'HP': 4780, 'ATK': 311.0, 'ATK%': 46.6, 'ER': 51.8, 'EM': 187.0,
        				 'PHYSICAL DMG': 58.3,  'CRIT RATE': 31.1, 'CRIT DMG': 62.2, 'ELEM': 46.6,
        				 'HP%': 46.6, 'DEF%': 58.3, 'HEAL BONUS': 35.9}


        max_subs = {'ATK': 19.0, 'EM': 23.0, 'ER': 6.5, 'ATK%': 5.8,
        				'CRIT RATE': 3.9, 'CRIT DMG': 7.8, 'DEF': 23.0, 'HP': 299.0, 'DEF%': 7.3, 'HP%': 5.8}

        elements = ['ANEMO', 'HYDRO', 'GEO', 'PYRO', 'CRYO', 'ELECTRO']

        sub_score = 0
        main = self.main if not list_check_entry(self.main[0], elements) else ['ELEM', self.main[1]]
        main_score = weights[main[0]] * 100 * (3 + self.lvl / 4)
        main_score = main_score if main_score > 0 else 100


        for key, value in self.subs:
            sub_score += value/max_subs[key] * weights[key] * 100


        score = main_score + sub_score
        max = 1650
        print(f'Gear score: {int(score)} ({(score * 100 / max):.2f}%)')

        self.gs = int(score)


async def get_blank_url(channel, blank):
    file = File(fp = blank.image_bytes, filename = "blank.png")
    message = await channel.send(file = file)
    return message.attachments[0].url
