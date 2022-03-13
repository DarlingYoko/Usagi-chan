import discord, pytz
import twitchAPI
from datetime import datetime
from discord.ext import commands, tasks
from time import mktime
from random import randint, choice, SystemRandom
from bin.functions import format_time, get_member_by_all, get_embed
from cogs.beer.extra import *
from twitchAPI.twitch import Twitch
from twitchAPI.types import AuthScope
from pprint import pprint
from copy import deepcopy


# 1. Каждый зареганный игрок получает в день N монет
# Раз в день надо написать комаду работа/завод чтобы получить монеты за N монет
# 2. Есть меню которое меняется каждый день
# 3. В меню есть пыво и закуски по X монет
# 4. Когда ты заказываешь пыво, Усаги наливает рандомное кол-во пыва и закусочку, далее снимает деньги в эквиваленте пыва, таким образом можно обонкроится если Усаги много нальёт
# 5. Возможность налить другу

# На стриме - фарм Усаги коинов
# можно конвертировать Усаги коины в Каки
# За Каки покупка пыва.
# Курс Каки К Усаги коинам в команду !курс
# Снимать дабаби при использовании дабаби и если нет дабаби то удалять сообщение

# Axonn в пивe

# Документация и покупка больше 1 позиции
# Функционал коллекторов 
# новые награды
# купить буст
# изменить что то на сервере
# оценка персонажа от Усаги
# игра в вордли раз в 4 часа
# за определенное кол во валюты можно давать какую нибудь роль, 
# которую можно всем тегать или что то типо того @ 
# либ самим покупать и придумывать роль человеку
# а соц пакет у нас будет? зп по выходным без работы например
# лимит упоминаний +
# рулетка на бан за 6666
# анонимные посылания нахуй 
# Возможность кинуть клеймо и снять с себя только за дабеби


class Beer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.prices = {
            'Пиво светлое': [100, 200],
            'Пиво тёмное': [100, 200],
            'Эль': [100, 200],
            'Дюшес': [100, 150],
            'Байкал': [100, 500],
            'Тархун': [100, 150],
            'Сидр': [100, 150],
            'Квас': [100, 150],
            'Морс': [100, 150],
            'Сидр': [100, 200],
        }
        self.additionals = {
            'Сушённая рыбка': [100, 100],
            'Кальмарчик': [200, 400],
            'Фисташки': [200, 500],
            'Жаренный арахис': [50, 200],
            'Чипсеки': [200, 300],
            'Кыр сосичка': [0, 100],
            'Гавно': [0, 50],
        }
        self.extras = {
            'Забить яблочко': [400, 600, buy_based_apple],
            'Послать Весдоса нахуй': [20, 50, send_wesdos_nahui],
            'Послать пользователя нахуй': [50, 70, anon_send_nahui],
            'Ебучая рулетка': [6666, 6666, ban_casino],
            # 'Жаренный арахис': [50, 200],
            # 'Чипсеки': [200, 300],
            # 'Кыр сосичка': [0, 100],
        }
        self.generate_menu.start()
        self.twitch_auth.start()
        self.check_rewards_twitch.start()
        self.wesdos_counter.start()
        
    @tasks.loop(minutes=1, count=1)
    async def twitch_auth(self):
        token = self.config['twitch']['token']
        refresh_token = self.config['twitch']['refresh_token']
        client_id = self.config['twitch']['client_id']
        client_secret = self.config['twitch']['client_secret']
        self.bot.twitch = Twitch(client_id, client_secret)
        target_scope = [AuthScope.CHANNEL_READ_REDEMPTIONS, AuthScope.CHANNEL_MANAGE_REDEMPTIONS]
        self.bot.twitch.set_user_authentication(token, target_scope, refresh_token)

    @tasks.loop(minutes=10)
    async def wesdos_counter(self):
        db_counter = self.bot.db.get_value('pivo', 'money', 'user_id', 1)
        if not db_counter:
            return
        channel = await self.bot.fetch_channel(951537014291976212)
        await channel.edit(name = f'{db_counter} раз')

    @wesdos_counter.before_loop
    async def before_wesdos_counter(self):
        print('waiting for wesdos_counter')
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24)
    async def generate_menu(self):
        prices = deepcopy(self.prices)
        additionals = deepcopy(self.additionals)

        menu = {'drinks':[], 'snacks': [], 'extra': list(self.extras.keys())}

        for i in range(3):
            pos = choice(list(prices.keys()))
            menu['drinks'].append(pos)
            del prices[pos]

        while len(menu['snacks']) != 2:
            pos = choice(list(additionals.keys()))
            if pos == 'Гавно':
                continue
            menu['snacks'].append(pos)
            del additionals[pos]

        # menu['Забить яблочко'] = [400, 600]
        menu['snacks'].append('Гавно')

        pprint(menu)
        self.menu = menu



    @commands.command(name='работа', aliases=['work', 'работать', 'батрачить', 'рабство'], description = 'Команда для зарабатывания <:dababy:949712395385843782>', help='toxic')
    # @commands.cooldown(per=60*60*24, rate=1, type=commands.BucketType.user)
    async def go_to_work(self, ctx):
        toxic = self.bot.config['channel'].getint('toxic')
        bar = self.bot.config['channel'].getint('bar')
        if ctx.channel.id not in [toxic, bar] and str(ctx.channel.type) == 'text':
            return await ctx.send(f'{ctx.author.mention}, Туть работать низя, выходи на смену туда -> <#{toxic}>')
        rng = SystemRandom()
        money = rng.randint(50, 100)
        user_id = ctx.author.id
        #  Проверка на возможность работать

        # Если нельзя работать, то сообщение об отмене

        # Если можно работать, то выдача монет + обновление в бд
        time = mktime(datetime.now().timetuple())
        values = self.bot.db.custom_command(f'SELECT money, last_time, streak from pivo where user_id = {user_id};')
        if values:
            # return await ctx.send(f'{ctx.author.mention}, Не получилось проверить твой паспорт, попробуй ещё раз!')
            values = values[0]
            last_money, last_time, streak = values[0], values[1], values[2]
            
            if last_time:
                diff = int(time - last_time)
                diff = 84600 - diff # если больше 0, то кд, если меньше нуля, но не меньше чем -86400, то день юза, если меньше чем -86400, то факап
                # diff = 0
                if diff > 0:
                    # user on cooldown
                    time = format_time(diff)
                    return await ctx.send(f'{ctx.author.mention}, Ты сможешь работать через {time}')
                elif diff <= 0 and diff > -84600:
                    # new work day
                    extra = ''
                    streak += 1
                    modifyer = 0
                    if streak in [10, 20, 30, 40]:
                        modifyer = streak * 10
                        extra = f'Также за хорошую работу ты получаешь премию {modifyer}'
                    if streak >= 50 and streak % 10 == 0:
                        modifyer = 1000
                        extra = f'Жесть ты работяга получай МЕГАХАРОШУЮ премию {modifyer}'
                    last_money += money
                    
                    r = self.bot.db.custom_command(f'UPDATE pivo set money = {last_money+modifyer}, last_time = {time}, streak = {streak} where user_id = {user_id};')
                    if r == 1:
                        return await ctx.send(f'{ctx.author.mention}, Хорошо поработал, дежи {money} <:dababy:949712395385843782> {extra}\nТеперь у тебя {last_money+modifyer} <:dababy:949712395385843782>, твой стрик {streak}')
                    else:
                        return await ctx.send(f'{ctx.author.mention}, Не получилось отправить тебя на работу, сходи ещё раз!')
                else:
                    # fuckup streak 
                    last_money += money
                    streak = 1
                    r = self.bot.db.custom_command(f'UPDATE pivo set money = {last_money}, last_time = {time}, streak = {streak} where user_id = {user_id};')
                    if r == 1:
                        return await ctx.send(f'{ctx.author.mention}, Понятно, дабаби закончились, так сразу на работу прибежал, ладно дежи свои {money} <:dababy:949712395385843782> и иди с миром\nТеперь у тебя {last_money} <:dababy:949712395385843782>, твой стрик {streak}')
                    else:
                        return await ctx.send(f'{ctx.author.mention}, Не получилось отправить тебя на работу, сходи ещё раз!')
        else:
            money += 50
            
            r = self.bot.db.insert('pivo', user_id, money, time, 1, 0, 0, 0, False, 0)
            if r == 1:
                await ctx.send(f'{ctx.author.mention}, Поздравляю с первым рабочим днём, твоя первая зарплата — {money} <:dababy:949712395385843782>')
            else:
                await ctx.send(f'{ctx.author.mention}, Не получилось отправить тебя на работу, сходи ещё раз!')

        # bd.update or insert
    @commands.command(name='меню', aliases=['menu'], description = 'Посмотреть меню на сегодня')
    @commands.cooldown(per=60*1, rate=1, type=commands.BucketType.user)
    async def today_menu(self, ctx):
        text_drinks = ''
        text_snacks = ''
        text_extra = ''
        counter = 1
        for key in self.menu['drinks']:
            text_drinks += f'{counter}. {key}\n'
            counter += 1
        for key in self.menu['snacks']:
            text_snacks += f'{counter}. {key}\n'
            counter += 1
        for key in self.menu['extra']:
            range_ = self.extras[key]
            text_extra += f'{counter}. {key} {range_[0]}-{range_[1]}\n'
            counter += 1
        fields = [
                {'name': 'Напитки', 
                    'value': text_drinks,
                    'inline': True},
                {'name': '_ _', 
                    'value': '_ _',
                    'inline': True},
                {'name': 'Закуски', 
                    'value': text_snacks,
                    'inline': True},
                {'name': 'Доп Услуги', 
                    'value': text_extra,
                    'inline': True},
        ]
        embed = get_embed(title='Меню на сегодня', description='[Описание всех пунктов меню](https://discord.com/channels/858053936313008129/951557489344806983)', fields=fields)
        await ctx.send(content='Нья!', embed=embed)

    @today_menu.error
    async def today_menu_errors(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            time = format_time(retry_after)
            await ctx.send(f'{ctx.author.mention}, Рановато для получения меню, я же недавно показывала его тебе, бака! Попробуй через {time}')

    @commands.command(
        name='купить', 
        aliases=['buy'], 
        description='Купить наименование себе или другану, для покупки указывайте номер лота. Возможно покупка только 1 лота за раз. Если хотите купить для друга, то укажите его ник в конце.',
        usage='<№ лота> <Имя или ID друга по желанию>',
        )
    # @commands.cooldown(per=60*1, rate=1, type=commands.BucketType.user)
    async def buy_beer(self, ctx, pos: int, *, for_user_name = None):
        pos -= 1
        answer = ''
        member = None
        len_extras = len(self.menu['extra'])
        len_prices = len(self.menu['drinks'])
        len_additionals = len(self.menu['snacks'])
        wesdos = False
        if pos >= 0 and pos <= len_prices - 1:
            product = self.menu['drinks'][pos]
            price = self.prices[product]
            answer = f'Ты налил выпить {product}а'
        elif pos >= len_prices and pos <= len_prices + len_additionals - 1:
            pos -= len_prices
            product = self.menu['snacks'][pos]
            price = self.additionals[product]
            answer = f'Ты купил {product}'
        elif pos >= len_prices + len_additionals and pos <= len_prices + len_additionals + len_extras - 1:
            pos -= (len_prices + len_additionals)
            if pos == 1:
                wesdos = True
            product = self.menu['extra'][pos]
            price = self.extras[product]
            answer = price[2]
        else:
            return await ctx.send(f'{ctx.author.mention}, Такого мы не продаём!')
        # await ctx.send(content=text_menu)
        if for_user_name != None:
            member = await get_member_by_all(self, for_user_name)
            if member == None:
                return await ctx.send(f'{ctx.author.mention}, Такого пользователя нет!')
            
        
       
        sell_count = randint(price[0], price[1])
        values = self.bot.db.custom_command(f'SELECT money, spend, count_of_purchases, count_of_purchases_for_user from pivo where user_id = {ctx.author.id};')
        if not values:
            return await ctx.send(f'{ctx.author.mention}, Не удалость получить твои <:dababy:949712395385843782>, попробуй позже!')
        values = values[0]
        money, spend, count_of_purchases, count_of_purchases_for_user = values[0], values[1], values[2], values[3] 
        if money < 1:
            return await ctx.send(f'{ctx.author.mention}, У тебя не хватает <:dababy:949712395385843782> на покупку!')
        if money < 1 or (money - sell_count < 0 and product == 'Ебучая рулетка'):
            return await ctx.send(f'{ctx.author.mention}, Пчел, ты хочешь рулетку, но делаешь это без <:dababy:949712395385843782>. Иди работай негодяй!')
        spend += sell_count
        if for_user_name and member:
            count_of_purchases_for_user += 1
        
        count_of_purchases += 1
        money -= sell_count
        r = self.bot.db.custom_command(f'UPDATE pivo set money = {money}, spend = {spend}, count_of_purchases = {count_of_purchases}, count_of_purchases_for_user = {count_of_purchases_for_user} where user_id = {ctx.author.id};')
        if r == 1:
            if type(answer) != str:
                if member == None:
                    member = ctx.author
                answer = await answer(self, ctx, member)
            if wesdos:
                db_counter = self.bot.db.get_value('pivo', 'money', 'user_id', 1)
                db_counter += 1
                self.bot.db.update('pivo', 'money', 'user_id', db_counter, 1)
            if for_user_name != None and member:
                answer = f'{answer} для {member.mention}'
            await ctx.send(f'{ctx.author.mention}, {answer} за {sell_count} <:dababy:949712395385843782>\nУ тебя осталось {money} <:dababy:949712395385843782>')
        else:
            await ctx.send(f'{ctx.author.mention}, Не получилось обработать твою покупку, попробуй позже!')


    @buy_beer.error
    async def buy_beer_errors(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.mention}, Ты не ввёл позицию!')
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f'{ctx.author.mention}, Ты ввёл неверную позицию!')
    
    # @commands.command()
    # async def test_ban(self, ctx):
    #     member = await ctx.guild.fetch_member(270904126974590976)
        

    @tasks.loop(minutes=1)
    async def check_rewards_twitch(self):
        reward_ids = [
            'af417b2f-0332-4265-8512-8814d05e4b60',
            '81665d97-6eec-412b-b511-cd50d22e336d',
            'd47d8290-ccef-4526-ac28-ff068643ad12',
            '418549d2-ceeb-4b2d-b584-d71649606d79',
            '76459db2-8bc9-43b7-900f-4eb6e00c3ccf',
        ]
        redemptions = []
        for reward_id in reward_ids:
            r = self.bot.twitch.get_custom_reward_redemption(
                broadcaster_id='557165958',
                reward_id=reward_id,
                status=twitchAPI.types.CustomRewardRedemptionStatus.UNFULFILLED
            )
            if 'data' in r.keys():
                for reward in r['data']:
                    user_input = reward['user_input']
                    user_name = reward['user_name']
                    cost = reward['reward']['cost']
                    title = reward['reward']['title']
                    redemption_id = reward['id']
                    member = await get_member_by_all(self, user_input)
                    if not member:
                        # reject reward
                        status = twitchAPI.types.CustomRewardRedemptionStatus.CANCELED
                    else:
                        # approve reward
                        status = twitchAPI.types.CustomRewardRedemptionStatus.FULFILLED
                    redemptions.append({'member': member,
                                            'from_user': user_name,
                                            'cost': cost, 
                                            'status': status,
                                            'redemption_id': redemption_id,
                                            'reward_id': reward_id})
                    print(user_input, user_name, cost, title, redemption_id, status)
        # pprint(redemptions)
        channel = await  self.bot.fetch_channel(858053937008214018)
        for redemption in redemptions:
            cost = redemption['cost']
            member = redemption['member']
            response = 0
            if member != None:
                money = self.bot.db.get_value('pivo', 'money', 'user_id', member.id)
                money += cost // 10
                response = self.bot.db.update('pivo', 'money', 'user_id', money, member.id)
                if not response:
                    redemption['status'] = twitchAPI.types.CustomRewardRedemptionStatus.CANCELED
            r = self.bot.twitch.update_redemption_status(
            broadcaster_id='557165958', 
            reward_id=redemption['reward_id'],
            redemption_ids=[redemption['redemption_id']],
            status=redemption['status'])

            print(r)
            
            if response:
                from_user = redemption['from_user']
                await channel.send(f'{member.mention}, Тебе перевод {cost//10} <:dababy:949712395385843782> от {from_user}')
        

    @check_rewards_twitch.before_loop
    async def before_check_rewards_twitch(self):
        print('waiting for twitch rewards')
        await self.bot.wait_until_ready()

    @commands.command(name='кэш', aliases=['кошелёк', 'кошелек', 'wallet', 'кеш', 'бабло', 'мани', 'зелень', 'капуста', 'cash', 'баланс'], description = 'Посмотреть свой кэш')
    async def get_user_wallet(self, ctx):
        money = self.bot.db.get_value('pivo', 'money', 'user_id', ctx.author.id)
        await ctx.send(content=f'{ctx.author.mention}, На твоём кошельке сейчас {money} <:dababy:949712395385843782>')

    @commands.cooldown(per=60*5, rate=1)
    @commands.command(name = 'топ_трат', description='Посмотреть на богатейших людей и самых больших транжир.')
    async def spend_top(self, ctx):
        pivo_table = self.bot.db.get_all('pivo')
        table = []
        for user in pivo_table:
            if user[0] == 1:
                continue
            try:
                member = await ctx.guild.fetch_member(user[0])
                member_name = member.name
            except:
                continue
            
            table.append([member_name, user[1], user[4], user[5], user[6]])
        top_money = sorted(table, key=lambda x: x[1], reverse=True)
        top_spend = sorted(table, key=lambda x: x[2], reverse=True)
        top_spend_for_self = sorted(table, key=lambda x: x[3], reverse=True)
        top_spend_for_user = sorted(table, key=lambda x: x[4], reverse=True)

        # print(top_spend)
        # print(top_spend_for_self)
        # print(top_spend_for_user)
        text_money = ''
        text_spend = ''
        text_spend_for_self = ''
        text_spend_for_user = ''
        counter = 1
        for user in top_money[:10]:
            text_money += f'{counter}. {user[0]} {user[1]}\n'
            counter += 1

        counter = 1
        for user in top_spend[:10]:
            text_spend += f'{counter}. {user[0]} {user[2]}\n'
            counter += 1

        counter = 1
        for user in top_spend_for_self[:10]:
            text_spend_for_self += f'{counter}. {user[0]} {user[3]}\n'
            counter += 1

        counter = 1
        for user in top_spend_for_user[:10]:
            text_spend_for_user += f'{counter}. {user[0]} {user[4]}\n'
            counter += 1

        fields = [
                {'name': 'Топ богачей', 
                    'value': text_money,
                    'inline': True},
                {'name': '_ _', 
                    'value': '_ _',
                    'inline': True},
                {'name': 'Топ транжир', 
                    'value': text_spend,
                    'inline': True},
                {'name': 'Топ покупателей', 
                    'value': text_spend_for_self,
                    'inline': True},
                {'name': '_ _', 
                    'value': '_ _',
                    'inline': True},
                {'name': 'Топ меценатов', 
                    'value': text_spend_for_user,
                    'inline': True},
        ]
        embed = get_embed(title='Топ топов', fields=fields)
        await ctx.send(content='Нья!', embed=embed)

    @spend_top.error
    async def spend_top_errors(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            time = format_time(retry_after)
            await ctx.send(f'{ctx.author.mention}, Рановато для получения топа, я же недавно показывала его вам, бака! Попробуй через {time}')

    @commands.command(name='часовая', aliases=['hourly', 'hw'], description = 'Команда для зарабатывания <:dababy:949712395385843782> раз в час', help='toxic')
    async def go_to_work_hourly(self, ctx):
        toxic = self.bot.config['channel'].getint('toxic')
        bar = self.bot.config['channel'].getint('bar')
        if ctx.channel.id not in [toxic, bar] and str(ctx.channel.type) == 'text':
            return await ctx.send(f'{ctx.author.mention}, Туть работать низя, выходи на смену туда -> <#{toxic}>')
        rng = SystemRandom()
        money = rng.randint(0, 25)
        user_id = ctx.author.id
        #  Проверка на возможность работать

        # Если нельзя работать, то сообщение об отмене

        # Если можно работать, то выдача монет + обновление в бд
        time = mktime(datetime.now().timetuple())
        values = self.bot.db.custom_command(f'SELECT money, hourly_work from pivo where user_id = {user_id};')
        if values:
            # return await ctx.send(f'{ctx.author.mention}, Не получилось проверить твой паспорт, попробуй ещё раз!')
            values = values[0]
            last_money, hourly_work = values[0], values[1]
            if hourly_work == None:
                hourly_work = 1
            
            if hourly_work:
                diff = int(time - hourly_work)
                diff = 3600 - diff # если больше 0, то кд, если меньше нуля, но не меньше чем -86400, то день юза, если меньше чем -86400, то факап
                # diff = 0
                if diff > 0:
                    # user on cooldown
                    time = format_time(diff)
                    return await ctx.send(f'{ctx.author.mention}, Твоя часовая смена через {time}')

                else:
                    # fuckup streak 
                    last_money += money
                    r = self.bot.db.custom_command(f'UPDATE pivo set money = {last_money}, hourly_work = {time} where user_id = {user_id};')
                    if r == 1:
                        return await ctx.send(f'{ctx.author.mention}, Часовая смена закончена, топай довольный с {money} <:dababy:949712395385843782>\nТеперь у тебя {last_money} <:dababy:949712395385843782>')
                    else:
                        return await ctx.send(f'{ctx.author.mention}, Не получилось отправить тебя на работу, сходи ещё раз!')
        else:
            
            r = self.bot.db.insert('pivo', user_id, money, 0, 1, 0, 0, 0, False, time)
            if r == 1:
                return await ctx.send(f'{ctx.author.mention}, Часовая смена закончена, топай довольный с {money} <:dababy:949712395385843782>\nТеперь у тебя {last_money} <:dababy:949712395385843782>')
            else:
                await ctx.send(f'{ctx.author.mention}, Не получилось отправить тебя на работу, сходи ещё раз!')

    @commands.command()
    @commands.is_owner()
    async def weekend(self, ctx):
        text = 'Всех с концом рабочей недели. Воть вам мини премия за неделю.\n ||+333||'
        users = self.bot.db.get_all('pivo')
        for user in users:
            if user[0] == 1:
                continue
            # text += f'<@{user[0]}, {user[1]}\n'
            r = self.bot.db.update('pivo', 'money', 'user_id', user[1]+333, user[0])
            print(r)
        
        # channel = await self.bot.fetch_channel(858053937008214018)
        await ctx.send(text)
            
        

    










    


def setup(bot):
    bot.add_cog(Beer(bot))