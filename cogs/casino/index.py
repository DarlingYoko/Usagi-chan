from re import A
from discord.ext import commands, tasks
from discord import File, SelectOption
from time import mktime
from datetime import datetime
from discord.ui import Modal, Select, InputText, Button
from bin.functions import get_embed, format_time
from random import SystemRandom, choice
from cogs.casino.extra import *
import asyncio
import discord

# Реализация рулетки:
# Один пользователь запускает рулетку, на вызов команды кд 10 минут
# Создание вьюшки и обратка пользователей



class Roulette_modal(Modal):
    def __init__(self, game, bet):
        super().__init__(title='Ставочка', custom_id='roulette_modal')
        self.bet = bet
        self.game = game
        if bet == 'own':
           self.add_item(InputText(label='Число, на которое ты хочешь поставить', custom_id='own_bet'))
        if bet == 'columns':
           self.add_item(InputText(label='Номер колонны', custom_id='own_bet')) 
        if bet == 'dozens':
           self.add_item(InputText(label='Номер дюжины', custom_id='own_bet')) 
        self.add_item(InputText(label='Ставка', custom_id='bet_count'))
        
    async def callback(self, interaction: discord.Interaction):

        if self.game.is_finished():
            return await interaction.response.send_message(content=f'Ты не успел поставить(', ephemeral=True)
        # if interaction.user.id in self.game.players.keys():
        #     return await interaction.response.send_message(content=f'Ты уже сделал ставку на эту игру, подожди пока она закончится или выбери другой стол!', ephemeral=True)

        own_bet = None
        if self.children[0].custom_id == 'own_bet':
            own_bet = self.children[0].value
            if not own_bet.isdecimal():
                return await interaction.response.send_message(content=f'Ты ввёл символы или буковы в поле "Выбор числа"!', ephemeral=True)
            own_bet = int(own_bet)
            if own_bet < 1 or own_bet > 36:
                return await interaction.response.send_message(content=f'Ты ввёл недопустимое число в поле "Выбор числа"!', ephemeral=True)
            bet = self.children[1].value
        else:
            bet = self.children[0].value
        
        if not bet.isdecimal():
            return await interaction.response.send_message(content=f'Ты ввёл символы или буковы в поле "Размер ставки"!', ephemeral=True)

        if self.bet in ['columns', 'dozens']:
            if own_bet < 1 or own_bet > 3:
                return await interaction.response.send_message(content=f'Ты ввёл не допустимое значние в поле "Колонна/Дюжина"!', ephemeral=True)

        bet = int(bet)
        # if bet < 1:
            # return await interaction.response.send_message(content=f'Ты ввёл недопустимое число в поле "Размер ставки"!', ephemeral=True)
        money = self.game.bot.db.get_value('pivo', 'money', 'user_id', interaction.user.id)
        if not money:
            return await interaction.response.send_message(content=f'У тебя нет <:dababy:949712395385843782> в банке!', ephemeral=True)
        
        if bet > money:
            return await interaction.response.send_message(content=f'Ты не можешь сделать ставку больше чем у тебя есть <:dababy:949712395385843782>!', ephemeral=True)
        # print(self.children[1].value, self.children[1].custom_id)
        money -= bet

        if interaction.user.id in self.game.players.keys():
            self.game.players[interaction.user.id].append({'type_bet': self.bet, 'bet': bet, 'own_bet': own_bet, 'name': interaction.user.name})
        else:
            self.game.players[interaction.user.id] = [{'type_bet': self.bet, 'bet': bet, 'own_bet': own_bet, 'name': interaction.user.name}]
        await interaction.response.send_message(content=f'Ты сделал ставку в размере {bet} <:dababy:949712395385843782> на {self.bet}', ephemeral=True)
        self.game.bot.db.update('pivo', 'money', 'user_id', money, interaction.user.id)


class Roulette_bet_select(Select['Roulette_view']):
    def __init__(self):
        options = [
            SelectOption(label='Красное', value='red'),
            SelectOption(label='Чёрное', value='black'),
            SelectOption(label='Зеро', value='zero'),
            SelectOption(label='Чётное', value='even'),
            SelectOption(label='Нечётное', value='odd'),
            SelectOption(label='Малые', value='little'),
            SelectOption(label='Большие', value='big'),
            SelectOption(label='Колонны', value='columns'),
            SelectOption(label='Дюжины', value='dozens'),
            SelectOption(label='Свой номер', value='own'),
        ]
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Roulette_view = self.view
        bet = self.values[0]
        await interaction.response.send_modal(Roulette_modal(view, bet))
            

class Roulette_view(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.players = {}
        self.bot = bot
        self.add_item(Roulette_bet_select())


class Blackjack_btn_join(Button['Blackjack_view']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, label='Войти')

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Blackjack_view = self.view
        user_id = interaction.user.id

        if user_id in view.players:
            return await interaction.response.send_message(content='Ты уже зарегестрирован на игру!', ephemeral=True)

        # view.players[user_id] = {'bet': None, 'name': interaction.user.name, 'action': None}
        # embed = get_embed(embed=view.embed, description=view.embed.description + f'{interaction.user.name}\n')
        # await interaction.message.edit(embed=embed)
        await interaction.response.send_modal(Blackjack_modal_make_bet(view))

class Blackjack_btn_leave(Button['Blackjack_view']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label='Выйти')

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Blackjack_view = self.view
        user_id = interaction.user.id

        if user_id not in view.players.keys():
            return await interaction.response.send_message(content='Ты ещё не зарегестрирован на игру!', ephemeral=True)

        del view.players[user_id]
        desc = view.embed.description.split('\n')
        name = interaction.user.name
        desc.remove(name)
        view.embed.description = '\n'.join(desc)
        await interaction.message.edit(embed=view.embed)

class Blackjack_btn_make_bet(Button['Blackjack_view']):
    def __init__(self):
        super().__init__(label='Сделать ставку')

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Blackjack_view = self.view
        # if interaction.user.id not in view.players.keys():
        #     return await interaction.response.send_message(content=f'Ты не зарегестрирован на игру, чтобы делать ставку!', ephemeral=True)
        await interaction.response.send_modal(Blackjack_modal_make_bet(view))

class Blackjack_btn_hit(Button['Blackjack_view']):
    def __init__(self, user_id):
        super().__init__(style=discord.ButtonStyle.success, label='Hit')
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Blackjack_view = self.view
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(content='Сейчас игра не с тобой', ephemeral=True)
        
        view.players[interaction.user.id]['action'] = 'hit'


class Blackjack_btn_stay(Button['Blackjack_view']):
    def __init__(self, user_id):
        super().__init__(label='Stay')
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Blackjack_view = self.view
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(content='Сейчас игра не с тобой', ephemeral=True)

        view.players[interaction.user.id]['action'] = 'stay'

        

class Blackjack_modal_make_bet(Modal):
    def __init__(self, view):
        super().__init__(title='Ставочка', custom_id='blackjack_modal_make_bet')
        self.add_item(InputText(label='Ставка', custom_id='bet_count'))
        self.game = view
    
    async def callback(self, interaction: discord.Interaction):
        if not self.game.reg:
            return await interaction.response.send_message(content=f'Ты не успел сделать ставку', ephemeral=True)
        bet = self.children[0].value
        
        if not bet.isdecimal():
            return await interaction.response.send_message(content=f'Ты ввёл символы или буковы в поле "Размер ставки"!', ephemeral=True)

        bet = int(bet)
        # if bet < 1:
            # return await interaction.response.send_message(content=f'Ты ввёл недопустимое число в поле "Размер ставки"!', ephemeral=True)
        money = self.game.bot.db.get_value('pivo', 'money', 'user_id', interaction.user.id)
        if not money:
            return await interaction.response.send_message(content=f'У тебя нет <:dababy:949712395385843782> в банке!', ephemeral=True)
        
        if bet > money:
            return await interaction.response.send_message(content=f'Ты не можешь сделать ставку больше чем у тебя есть <:dababy:949712395385843782>!', ephemeral=True)

        money -= bet

        
        self.game.players[interaction.user.id] = {'bet': bet, 'name': interaction.user.name, 'action': None}
        embed = get_embed(embed=self.game.embed, description=self.game.embed.description + f'{interaction.user.name}\n')
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(content=f'Ты сделал ставку в размере {bet} <:dababy:949712395385843782>', ephemeral=True)
        # self.game.bot.db.update('pivo', 'money', 'user_id', money, interaction.user.id)
        


class Blackjack_view(discord.ui.View):
    def __init__(self, bot, embed):
        super().__init__()
        self.players = {}
        self.bot = bot
        self.embed = embed
        self.reg = True
        self.add_item(Blackjack_btn_join())
        self.add_item(Blackjack_btn_leave())
        # self.add_item(Blackjack_btn_make_bet())

    


        


class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.roulettes = []
        self.blackjack_games = []
        self.ready_game = True
        self.roulette_counter.start()
        self.blackjack_counter.start()
        self.RED = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        self.BLACK = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
        self.columns = {1: range(1, 36, 3), 2: range(2, 36, 3), 3: range(3, 37, 3)}
        self.dozens = {1: range(1, 13), 2: range(13, 25), 3: range(25, 37)}
    

    @commands.cooldown(per=60, rate=1)
    @commands.command(name='рулетка', aliases=['roulette'])
    async def roulette(self, ctx):
        if not self.ready_game:
            return await ctx.send(f'{ctx.author.mention}, Сейчас нельзя создавать игры, я обновляюсь!')

        roulette_game = Roulette_view(ctx.bot)

        timer = int(mktime(datetime.now().timetuple()) + 60*2+20)
        image_url = 'https://media.discordapp.net/attachments/807349536321175582/951940401852452944/roulette-table-vector-20671332.png'
        embed = get_embed(title='Новая рулетка!', 
            description=f'Старт <t:{timer}:R>\nСкорее делайте ваши ставочки!',
            url_image=image_url)
        
        message = await ctx.send(embed=embed, view=roulette_game)
        self.roulettes.append({'message': message, 'embed': embed, 'game': roulette_game, 'timer': 60*2})
        await ctx.message.delete()

    @tasks.loop(seconds=1)
    async def roulette_counter(self):
        remove = []
        for message in self.roulettes:
            message['timer'] -= 1
            if message['timer'] == 0:
                message['game'].stop()
                gif_url = 'https://media.discordapp.net/attachments/807349536321175582/951805421050544138/1VNB.gif'
                embed = get_embed(embed=message['embed'],
                    description='Все ставки приняты, больше ставки не принимаются!\nКрутим рулетку!',
                    url_image=gif_url)
                await message['message'].edit(embed=embed, view=None)
                rng = SystemRandom()
                result = rng.randint(0, 36)
                if result in self.BLACK:
                    color = '\⚫'
                elif result in self.RED:
                    color = '\🔴'
                else:
                    color = '\🟢'
                
                winners = 'Победители:\n'
                losers = 'Проигравшие:\n'
                money_sql = ''
                stat_sql = ''
                trans_sql = ''
                for player_id, bets in message['game'].players.items():
                    for bet_data in bets:
                        type_bet = bet_data['type_bet']
                        bet = bet_data['bet']
                        own_bet = bet_data['own_bet']
                        name = bet_data['name']
                        if own_bet:
                            text = f'на число {own_bet}\n'
                        else:
                            text = '\n'

                        if (type_bet == 'even' and result % 2 == 0) or \
                            (type_bet == 'odd' and result % 2 == 1) or \
                            (type_bet == 'zero' and result == 0) or \
                            (type_bet == 'own' and result == own_bet) or \
                            (type_bet == 'red' and result in self.RED) or \
                            (type_bet == 'black' and result in self.BLACK) or \
                            (type_bet == 'little' and result >= 1 and result <= 18) or \
                            (type_bet == 'big' and result >= 19 and result <= 36) or \
                            (type_bet == 'columns' and result in self.columns[own_bet]) or \
                            (type_bet == 'dozens' and result in self.dozens[own_bet]):
                            
                            winners += f'{name}, поставил {bet}<:dababy:949712395385843782> на {type_bet} {text}'

                            if type_bet in ['even', 'odd', 'red', 'black', 'little', 'big']:
                                bet *= 2
                            elif type_bet in ['zero', 'own']:
                                bet *= 36
                            elif type_bet in ['columns', 'dozens']:
                                bet *= 3
                            else:
                                bet *= 0
                            money_sql += f'update pivo set money = money + {bet} where user_id = {player_id};\n'
                            stat_sql += f'update roulette_stat set win = win + {bet}, win_count = win_count + 1 where user_id = {player_id};\n'
                            trans_sql += f'insert into transactions values ({player_id}, {bet}, \'win bet\', \'\', {mktime(datetime.now().timetuple())});\n'
                                
                        else:
                            losers += f'{name}, поставил {bet}<:dababy:949712395385843782> на {type_bet} {text}'
                            money_sql += f'update pivo set spend = spend + {bet} where user_id = {player_id};\n'
                            stat_sql += f'update roulette_stat set lose = lose + {bet}, lose_count = lose_count+1 where user_id = {player_id};\n'
                            trans_sql += f'insert into transactions values ({player_id}, {bet}, \'lose bet\', \'\', {mktime(datetime.now().timetuple())});\n'
                self.bot.db.custom_command(money_sql)
                self.bot.db.custom_command(stat_sql)
                self.bot.db.custom_command(trans_sql)


                await asyncio.sleep(5)
                final_url = 'https://media.discordapp.net/attachments/807349536321175582/951946592968130561/3.png'
                embed = get_embed(embed=embed,
                    title='Рулетка закончена',
                    description=f'Выпало {result}{color}!\n{winners}\n\n{losers}',
                    url_image=final_url)
                await message['message'].edit(embed=embed)
                remove.append(message)
        for msg in remove:
            self.roulettes.remove(msg)

    @roulette.error
    async def roulette_errors(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            time = format_time(retry_after)
            await ctx.send(f'{ctx.author.mention}, Рановато для новой рулетки, подожди пока закончится предыдущая! Попробуй через {time}')

    @commands.command()
    @commands.is_owner()
    async def set_game(self, ctx, game = None):
        if game in ['1', 'true']:
            self.ready_game = True
            await ctx.send(f'{ctx.author.mention}, включила игры')
        else:
            self.ready_game = False
            await ctx.send(f'{ctx.author.mention}, выключила игры')

    @commands.cooldown(per=60*5, rate=1)
    @commands.command(name='победители')
    async def winners(self, ctx):
        pivo_table = self.bot.db.get_all('roulette_stat')
        table = []
        for user in pivo_table:
            if user[0] == 1:
                continue
            try:
                member = await ctx.guild.fetch_member(user[0])
                member_name = member.name
            except:
                continue
            
            table.append([member_name, user[1], user[2], user[3], user[4]])
        top_win = sorted(table, key=lambda x: x[1], reverse=True)
        top_win_count = sorted(table, key=lambda x: x[3], reverse=True)
        top_lose = sorted(table, key=lambda x: x[2], reverse=True)
        top_lose_count = sorted(table, key=lambda x: x[4], reverse=True)

        # print(top_spend)
        # print(top_spend_for_self)
        # print(top_spend_for_user)
        text_money = ''
        text_spend = ''
        text_spend_for_self = ''
        text_spend_for_user = ''
        counter = 1
        for user in top_win[:10]:
            text_money += f'{counter}. {user[0]} {user[1]}\n'
            counter += 1

        counter = 1
        for user in top_win_count[:10]:
            text_spend += f'{counter}. {user[0]} {user[3]}\n'
            counter += 1

        counter = 1
        for user in top_lose[:10]:
            text_spend_for_self += f'{counter}. {user[0]} {user[2]}\n'
            counter += 1

        counter = 1
        for user in top_lose_count[:10]:
            text_spend_for_user += f'{counter}. {user[0]} {user[4]}\n'
            counter += 1

        fields = [
                {'name': 'Топ лутателей', 
                    'value': f'```\n{text_money}```',
                    'inline': True},
                {'name': '_ _', 
                    'value': '_ _',
                    'inline': True},
                {'name': 'Топ лакеров', 
                    'value': f'```\n{text_spend}```',
                    'inline': True},
                {'name': 'Топ транжир', 
                    'value': f'```\n{text_spend_for_self}```',
                    'inline': True},
                {'name': '_ _', 
                    'value': '_ _',
                    'inline': True},
                {'name': 'Топ лузеров', 
                    'value': f'```\n{text_spend_for_user}```',
                    'inline': True},
        ]
        embed = get_embed(title='Топ топов', fields=fields)
        await ctx.send(content='Нья!', embed=embed)

    @winners.error
    async def winners_errors(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            time = format_time(retry_after)
            await ctx.send(f'{ctx.author.mention}, Рановато для получения топа, я же недавно показывала его вам, бака! Попробуй через {time}')

    
    @commands.group(
        name='правила',
        aliases=['rules'],
        description='Помощь по всем правилам казиныча'
    )
    async def rules(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('rules')
    

    @rules.command(name='рулетка')
    async def rules_roulette(self, ctx):
        await ctx.send(f'Вот ссылочка на все правила, ня\nhttps://discord.com/channels/858053936313008129/951577300758036630/954012390305984572')

    @commands.cooldown(per=60, rate=1, type=commands.BucketType.channel)
    @commands.command(name='блекджек', aliases = ['blackjack', 'bj'])
    async def blackjack(self, ctx):
        if not self.ready_game:
            return await ctx.send(f'{ctx.author.mention}, Сейчас нельзя создавать игры, я обновляюсь!')
        # 1. Когда игра стартует, происходит запись на игру примерно 30 сек + 
        # 2. Потом стартует сама игра с теми кто записался + 
        # 3. Раздача по две карты в открытую для игроков и 1/1 карты диллеру + 
        # 3.5 Проверка bj у диллера
        # 4. Ход игроков + 
        # 5. Ход диллера, если меньше 16 сумма то добор если 17 и больше то конец игры и подсчет очков
        timer = int(mktime(datetime.now().timetuple()) + 30)
        embed = get_embed(title='Новая игра в Блекджек!', description=f'Игра начнётся <t:{timer}:R>\nИгроки:\n')
        blackjack_game = Blackjack_view(ctx.bot, embed)
        message = await ctx.send(content='**Старт игры**\nДелайте свои ставки!', embed=embed, view=blackjack_game)
        self.blackjack_games.append({'message': message, 'embed': embed, 'game': blackjack_game, 'timer': 30})

    @blackjack.error
    async def blackjack_errors(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            time = format_time(retry_after)
            await ctx.send(f'{ctx.author.mention}, Рановато для нового стола блекджека, подожди пока закончится предыдущий! Попробуй через {time}')

    @tasks.loop(seconds=1)
    async def blackjack_counter(self):
        remove = []
        for message in self.blackjack_games:
            message['timer'] -= 1
            if message['timer'] == 0:
                game = message['game']
                embed = message['embed']
                channel = message['message'].channel
                msg = message['message']
                game.clear_items()
                # names = '\n'.join(list(map(lambda x: x['name'], game.players.values())))
                # players_ping = '\n'.join(list(map(lambda x: f'<@{x}>', game.players.keys())))
                # timer = int(mktime(datetime.now().timetuple()) + 30)
                # embed.description = f'<t:{timer}:R>\nИгроки\n{names}'
                
                # await message['message'].edit(content=f'**Старт игры**\nДелайте свои ставки!\n{players_ping}', embed=embed, view=game)
                # await asyncio.sleep(20)
                game.reg = False
                dealer = Player_bj()

                # Раздача карт

                fields = [{'name': 'Диллер' + ' | ' + str(dealer.calculate_value(1)),
                        'value': f"{dealer.cards[0]['pic']} <:cardback:955880197826158683>",
                        'inline': False}]
                remove_users = []

                for player_id, data in game.players.items():
                    if data['bet'] == 0 or data['bet'] == None:
                        await channel.send(f'<@{player_id}>, Ты сделал нулевую ставку и не учавствуешь в игре.')
                        remove_users.append(player_id)
                        continue

                    player = Player_bj()
                    data['player'] = player
                    cards = ' '.join(map(lambda x: x['pic'], player.cards))
                    fields.append({'name': data['name'] + ' | ' + str(player.calculate_value()),
                        'value': f"Ставка: {data['bet']}\n{cards}",
                        'inline': True})
                timer = int(mktime(datetime.now().timetuple()) + 30)
                embed.description = f'<t:{timer}:R>\nТекущий стол:'
                embed = get_embed(embed=embed, fields=fields)
                await message['message'].edit(content='Осмотр стола', embed=embed, view=None)
                for id in remove_users:
                    del game.players[id]
                await asyncio.sleep(10)
                can_play = True
                # Игра с проверкой бж у дилера
                if dealer.cards[0]['id'] in ['10', 'jack', 'queen', 'king', 'ace']:
                    embed.description = f'У диллера возможен блекджек! Проверям вторую карту'
                    await message['message'].edit(content=None, embed=embed)
                    await asyncio.sleep(5)
                    if dealer.calculate_value() == 21: 
                        dealer_field = fields[0]
                        dealer_field['value'] = ' '.join(map(lambda x: x['pic'], dealer.cards))
                        dealer_field['name'] = 'Дилер | 21'
                        embed.description = f'У диллера блекджек! Сразу переходим к подсчёту очков'
                        await message['message'].edit(embed=embed)
                        can_play = False
                        await asyncio.sleep(5)
                    else:
                        embed.description = f'У диллера не блекджек, играем дальше!'
                        await message['message'].edit(embed=embed)
                        await asyncio.sleep(5)
                new_msg = message['message']
                if can_play:
                    for player_id, data in game.players.items():
                        embed.description = f'Текущая раздача:'
                        game.clear_items()
                        game.add_item(Blackjack_btn_hit(player_id))
                        game.add_item(Blackjack_btn_stay(player_id))
                        old_msg = new_msg
                        await old_msg.delete()
                        new_msg = await channel.send(content=f'Играем с <@{player_id}>', embed=embed, view=game)
                        counter = 0
                        player = data['player']
                        while counter != 60 and player.calculate_value() < 21 and len(player.cards) < 6:
                            if data['action'] == 'hit':
                                data['action'] = None
                                counter = 0
                                for field in fields:
                                    if data['name'] in field['name']:
                                        player.cards.append(player.gen_card())
                                        
                                        field['value'] = 'Ставка: ' + str(data['bet']) + '\n' + ' '.join(map(lambda x: x['pic'], player.cards))
                                        field['name'] = data['name'] + ' | ' + str(player.calculate_value())
                                        embed = get_embed(embed=embed, fields=fields)
                                        await new_msg.edit(embed=embed)

                            elif game.players[player_id]['action'] == 'stay':
                                break
                            else:
                                pass
                            counter += 1
                            await asyncio.sleep(1)
                        if player.calculate_value() > 21:
                            await channel.send(f'<@{player_id}>, Ты набрал больше 21 и проиграл!')
                        if len(player.cards) == 6:
                            await channel.send(f'<@{player_id}>, Нельзя брать больше 6 карт!')

                # Ход диллера
                dealer_field = fields[0]
                dealer_field['value'] = ' '.join(map(lambda x: x['pic'], dealer.cards))
                dealer_field['name'] = 'Дилер | ' + str(dealer.calculate_value())
                embed.description = f'Ход дилера!'
                embed = get_embed(embed=embed, fields=fields)
                await new_msg.edit(embed=embed)
                await asyncio.sleep(1)
                while dealer.calculate_value() <= 16:
                    dealer.cards.append(dealer.gen_card())    
                    dealer_field['value'] = ' '.join(map(lambda x: x['pic'], dealer.cards))
                    dealer_field['name'] = 'Дилер | ' + str(dealer.calculate_value())
                    embed = get_embed(embed=embed, fields=fields)
                    await new_msg.edit(embed=embed)
                    await asyncio.sleep(1)

                # Подсчёт очков
                embed.description = f'Подсчёт очков'
                await new_msg.edit(content=None, embed=embed, view=None)
                dealer_number = dealer.calculate_value()
                sql = ''
                stat_sql = ''
                trans_sql = ''
                for player_id, data in game.players.items():
                    for field in fields:
                        if data['name'] in field['name']:
                            player = data['player']
                            bet = data['bet']
                            player_number = player.calculate_value()
                            if player_number > 21:
                                result = 'Перебор'
                                sql += f'update pivo set money = money - {bet}, spend = spend + {bet} where user_id = {player_id};\n'
                                stat_sql += f'update roulette_stat set lose = lose + {bet}, lose_count = lose_count+1 where user_id = {player_id};\n'
                                trans_sql += f'insert into transactions values ({player_id}, {bet}, \'lose bet\', \'\', {mktime(datetime.now().timetuple())});\n'
                            else:
                                if player_number == 21 and len(player.cards) == 2:
                                    result = 'Блекджек!'
                                    sql += f'update pivo set money = money + {bet*1.5} where user_id = {player_id};\n'
                                    stat_sql += f'update roulette_stat set win = win + {bet*1.5}, win_count = win_count+1 where user_id = {player_id};\n'
                                    trans_sql += f'insert into transactions values ({player_id}, {bet}, \'win bet\', \'\', {mktime(datetime.now().timetuple())});\n'
                                elif player_number > dealer_number or dealer_number > 21:
                                    result = 'Победа'
                                    sql += f'update pivo set money = money + {bet} where user_id = {player_id};\n'
                                    stat_sql += f'update roulette_stat set win = win + {bet}, win_count = win_count+1 where user_id = {player_id};\n'
                                    trans_sql += f'insert into transactions values ({player_id}, {bet}, \'win bet\', \'\', {mktime(datetime.now().timetuple())});\n'
                                elif dealer_number == player_number:
                                    result = 'Равно'
                                else:
                                    result = 'Мало'
                                    sql += f'update pivo set money = money - {bet}, spend = spend + {bet} where user_id = {player_id};\n'
                                    stat_sql += f'update roulette_stat set lose = lose + {bet}, lose_count = lose_count+1 where user_id = {player_id};\n'
                                    trans_sql += f'insert into transactions values ({player_id}, {bet}, \'lose bet\', \'\', {mktime(datetime.now().timetuple())});\n'
                            
                            field['name'] = field['name'] + '\n' + result
                
                embed = get_embed(embed=embed, fields=fields)
                await new_msg.edit(embed=embed)

    
                self.bot.db.custom_command(sql)
                self.bot.db.custom_command(stat_sql)
                self.bot.db.custom_command(trans_sql)


                remove.append(message)
        
        for msg in remove:
            self.blackjack_games.remove(msg)





        

        



        


def setup(bot):
    bot.add_cog(Casino(bot))