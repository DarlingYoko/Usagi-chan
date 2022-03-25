from copy import deepcopy
from random import shuffle
from datetime import datetime
from time import mktime
from bin.functions import get_embed
from time import mktime
from datetime import datetime
from discord.ui import Modal, InputText, Button
import asyncio, discord

CARDS = [{'2': ['<:01:955875487002005554>', '<:14:955875487140433960>', '<:27:955875486687428661>', '<:40:955875486913945692>']}, 
            {'3': ['<:02:955875486964260944>', '<:15:955875487153000468>', '<:28:955875486783926293>', '<:41:955892980617728010>']}, 
            {'4': ['<:03:955875486985252974>', '<:16:955875487228506173>', '<:29:955875486754537523>', '<:42:955875486972641281>']}, 
            {'5': ['<:04:955875486951682168>', '<:17:955875487165599844>', '<:30:955875487098482778>', '<:43:955875486922338335> ']}, 
            {'6': ['<:05:955875486968459284>', '<:18:955875487035568178>', '<:31:955875487203356783>', '<:44:955875487283019846>']}, 
            {'7': ['<:06:955875487039770754>', '<:19:955875487253680190>', '<:32:955875486830034945>', '<:45:955875487375298601>']}, 
            {'8': ['<:07:955875487027175484>', '<:20:955875487127851058>', '<:33:955875487236911114>', '<:46:955875487354322964>']}, 
            {'9': ['<:08:955875486846812251>', '<:21:955875487106883614>', '<:34:955875487354331206>', '<:47:955875487236915210> ']}, 
            {'10': ['<:09:955875487136231485>', '<:22:955875487085908028>', '<:35:955875487203328050>', '<:48:955875487194947665>']},  
            {'jack': ['<:10:955875487199154276>', '<:23:955875486934892545>', '<:36:955891579929911326>', '<:49:955893071550238771>']}, 
            {'queen': ['<:11:955875487123644477>', '<:24:955875486804893710>', '<:37:955875487207534612>', '<:50:955893134418649178>']}, 
            {'king': ['<:12:955875486679072850>', '<:25:955875487048163329>', '<:38:955875487010418729>', '<:51:955887623807844502>']}, 
            {'ace': ['<:00:955880097989156947>', '<:13:955875486997835867>', '<:26:955875487224311978>', '<:39:955875487027171439>']}]
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
        if bet < 1:
            return await interaction.response.send_message(content=f'Ты ввёл недопустимое число в поле "Размер ставки"!', ephemeral=True)
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
        

    async def start_game(self, data, message):
        await asyncio.sleep(30)
        await bj_game(data, message)

class Player_bj:
    def __init__(self, deck):
        self.deck = deck
        self.cards = [self.gen_card(), self.gen_card()]
    
    def calculate_value(self, slice = None):
        value = 0
        ace = 0
        for card in self.cards[:slice]:
            card = card['id']
            if card.isdecimal():
                value += int(card)
            elif card in ['jack', 'queen', 'king']:
                value += 10
            elif card == 'ace':
                value += 11
                ace += 1

            else:
                pass
        while ace > 0 and value > 21:
            value -= 10
            ace -= 1
        return value

    def gen_card(self):
        card = self.deck.pop(0)
        id = list(card.keys())[0]
        pic = card[id].pop(0)
        card[id].append(pic)
        self.deck.append(card)
        return {'id': id, 'pic': pic}


def gen_deck(pl_count):
    modifyer = 2
    if pl_count > 3:
        modifyer = 4

    deck = deepcopy(CARDS) * modifyer
    for i in range(10):
        shuffle(deck)

    for card in deck:
        id = list(card.keys())[0]
        # print(id)
        shuffle(card[id])
    
    return deck


async def bj_game(self, message):
    game = message['game']
    embed = message['embed']
    channel = message['message'].channel
    channel_id = channel.id
    game.clear_items()
    game.reg = False
    pl_count = len(list(game.players.keys()))
    # для 2-ух надо 104 карты
    # для 4 и более надо 208 карт
    if (not self.decks[channel_id]['deck']) or \
            (len(self.decks[channel_id]['deck']) == 26 and pl_count > 3) or \
            (len(self.decks[channel_id]['deck']) == 52 and pl_count < 4):
        self.decks[channel_id]['deck'] = gen_deck(pl_count)
    
    deck = self.decks[channel_id]['deck']
 
    dealer = Player_bj(deck)

    await channel.send(content=f'Создана колода на {len(self.decks[channel_id]["deck"]) * 4} карт')

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

        player = Player_bj(deck)
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

    self.decks[channel_id]['counter'] += 1
    if (len(self.decks[channel_id]['deck']) == 104 and self.decks[channel_id]['counter'] == 1) or \
            (len(self.decks[channel_id]['deck']) == 208 and self.decks[channel_id]['counter'] == 4):
        self.decks[channel_id]['deck'] = gen_deck(pl_count)


