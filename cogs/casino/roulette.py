from discord import SelectOption
from time import mktime
from datetime import datetime
from discord.ui import Modal, Select, InputText
from bin.functions import get_embed
from random import SystemRandom
import asyncio, discord

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

    async def start_game(self, data, message):
        await asyncio.sleep(60*2)
        self.stop()
        await roulette_game(data, message)


async def roulette_game(self, message):
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
