from copy import deepcopy
from datetime import datetime
from time import mktime
from bin.functions import get_embed
from time import mktime
from datetime import datetime
from random import SystemRandom, randint
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
        player = view.find_player(interaction.user.id)

        if player:
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
        player = view.find_player(interaction.user.id)

        if not player:
            return await interaction.response.send_message(content='Ты ещё не зарегестрирован на игру!', ephemeral=True)

        view.players.remove(player)
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
    def __init__(self, player):
        super().__init__(style=discord.ButtonStyle.success, label='Hit')
        self.player = player

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Blackjack_view = self.view
        if interaction.user.id != self.player.id:
            return await interaction.response.send_message(content='Сейчас игра не с тобой', ephemeral=True)

        self.player.action = 'hit'


class Blackjack_btn_stay(Button['Blackjack_view']):
    def __init__(self, player):
        super().__init__(label='Stay')
        self.player = player

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Blackjack_view = self.view
        if interaction.user.id != self.player.id:
            return await interaction.response.send_message(content='Сейчас игра не с тобой', ephemeral=True)

        self.player.action = 'stay'

class Blackjack_btn_surrender(Button['Blackjack_view']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label='SURRENDER')

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Blackjack_view = self.view
        player = view.find_player(interaction.user.id)
        if not player:
            return await interaction.response.send_message(content='Ты не играешь!', ephemeral=True)
        player.action = 'surrender'
        await interaction.response.send_message(content='Ты сдался и теряешь только половину ставки!', ephemeral=True)

class Blackjack_btn_double(Button['Blackjack_view']):
    def __init__(self, player):
        super().__init__(style=discord.ButtonStyle.primary, label='Double')
        self.player = player

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Blackjack_view = self.view
        if interaction.user.id != self.player.id:
            return await interaction.response.send_message(content='Сейчас игра не с тобой', ephemeral=True)

        self.player.action = 'double'

class Blackjack_btn_split(Button['Blackjack_view']):
    def __init__(self, player):
        super().__init__(style=discord.ButtonStyle.primary, label='Split')
        self.player = player

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Blackjack_view = self.view
        if interaction.user.id != self.player.id:
            return await interaction.response.send_message(content='Сейчас игра не с тобой', ephemeral=True)

        self.player.action = 'split'

class Blackjack_modal_make_bet(Modal):
    def __init__(self, view):
        super().__init__(title='Ставочка', custom_id='blackjack_modal_make_bet')
        self.add_item(InputText(label='Ставка', custom_id='bet_count'))
        self.game = view
    
    async def callback(self, interaction: discord.Interaction):
        player = self.game.find_player(interaction.user.id)

        if player:
            return await interaction.response.send_message(content='Ты уже зарегестрирован на игру!', ephemeral=True)
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

        player = Player_bj(interaction.user.id, interaction.user.name, bet)
        self.game.players.append(player)
        embed = get_embed(embed=self.game.embed, description=self.game.embed.description + f'{interaction.user.name}\n')
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(content=f'Ты сделал ставку в размере {bet} <:dababy:949712395385843782>', ephemeral=True)
        # self.game.bot.db.update('pivo', 'money', 'user_id', money, interaction.user.id)

class Blackjack_view(discord.ui.View):
    def __init__(self, bot, embed):
        super().__init__()
        self.players = []
        self.bot = bot
        self.embed = embed
        self.reg = True
        self.add_item(Blackjack_btn_join())
        self.add_item(Blackjack_btn_leave())
        # self.add_item(Blackjack_btn_make_bet())

    def find_player(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player
        return None
        

    async def start_game(self, data, message):
        await asyncio.sleep(30)
        await bj_game(data, message)

class Player_bj:
    def __init__(self, id=None, name=None, bet=None):
        self.id = id
        self.name = name
        self.bet = bet
        self.action = None
        self.cards = []
        # self.deck = deck

    
    def get_cards(self, owner=None):
        if not owner:
            self.cards = [self.gen_card(), self.gen_card()]
        else:
            self.cards = [{'id': '2', 'pic': '<:01:955875487002005554>'}, {'id': '2', 'pic': '<:14:955875487140433960>'}]
        
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
    
    def same_cards(self):
        card_1 = self.transform_card(self.cards[0]['id'])
        card_2 = self.transform_card(self.cards[1]['id'])
        return card_1 == card_2

    def transform_card(self, card):
        if card.isdecimal():
            card = int(card)
        elif card in ['jack', 'queen', 'king']:
            card = 10
        else:
            card = 11
        return card

def shuffle(deck):
    new_deck = []
    length = len(deck) - 1
    rng = SystemRandom()
    for i in range(length):
        index = rng.randint(0, length)
        new_deck.append(deck.pop(index))
        length -= 1
    new_deck.append(deck.pop(0))
    return new_deck



def gen_deck(pl_count):
    modifyer = 2
    if pl_count > 3:
        modifyer = 4

    deck = deepcopy(CARDS) * modifyer
    for i in range(randint(1, 10)):
        deck = shuffle(deck)


    for card in deck:
        id = list(card.keys())[0]
        # print(id)
        card[id] = shuffle(card[id])
    
    return deck


async def bj_game(self, message):
    game = message['game']
    embed = message['embed']
    channel = message['message'].channel
    channel_id = channel.id
    game.clear_items()
    game.reg = False
    sql = ''
    stat_sql = ''
    trans_sql = ''
    pl_count = len(game.players)
    # для 2-ух надо 104 карты
    # для 4 и более надо 208 карт
    if (not self.decks[channel_id]['deck']) or \
            (len(self.decks[channel_id]['deck']) == 26 and pl_count > 3) or \
            (len(self.decks[channel_id]['deck']) == 52 and pl_count < 4):
        self.decks[channel_id]['deck'] = gen_deck(pl_count)
    
    deck = self.decks[channel_id]['deck']
 
    dealer = Player_bj()
    dealer.deck = deck
    dealer.get_cards()

    # Раздача карт

    fields = [{'name': 'Диллер' + ' | ' + str(dealer.calculate_value(1)),
            'value': f"{dealer.cards[0]['pic']} <:cardback:955880197826158683>",
            'inline': False}]
    remove_users = []

    for player in game.players:
        if player.bet == 0 or player.bet == None:
            await channel.send(f'<@{player.id}>, Ты сделал нулевую ставку и не учавствуешь в игре.')
            remove_users.append(player)
            continue
        player.deck = deck
        # if player.id in [290166276796448768, 793409024015073281]:
        #     player.get_cards(1)
        # else:
        player.get_cards()
        cards = ' '.join(map(lambda x: x['pic'], player.cards))
        fields.append({'name': player.name + ' | ' + str(player.calculate_value()),
            'value': f'Ставка: {player.bet}\n{cards}',
            'inline': True})
    timer = int(mktime(datetime.now().timetuple()) + 30)
    embed.description = f'<t:{timer}:R>\nТекущий стол:'
    embed = get_embed(embed=embed, fields=fields)
    game.clear_items()
    game.add_item(Blackjack_btn_surrender())
    await message['message'].edit(content=f'Колода на {len(self.decks[channel_id]["deck"]) * 4} карт\nОсмотр стола', embed=embed, view=game)
    for user in remove_users:
        game.players.remove(user)

    # also time for surrender 
    await asyncio.sleep(20)
    remove = []
    for player in game.players:
        if player.action == 'surrender':
            sql += f'update pivo set money = money - {player.bet//2}, spend = spend + {player.bet//2} where user_id = {player.id};\n'
            stat_sql += f'update roulette_stat set lose = lose + {player.bet//2}, lose_count = lose_count+1 where user_id = {player.id};\n'
            trans_sql += f'insert into transactions values ({player.id}, {player.bet//2}, \'lose bet\', \'\', {mktime(datetime.now().timetuple())});\n'
            field = fields[game.players.index(player) + 1]
            fields.remove(field)
            embed = get_embed(embed=embed, fields=fields)
            await message['message'].edit(embed=embed)
            remove.append(player)
    for user in remove:
        game.players.remove(user)

    can_play = True
    await message['message'].edit(embed=embed, view=None)
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
        for player in game.players:
            embed.description = f'Текущая раздача:'

            game.clear_items()
            game.add_item(Blackjack_btn_hit(player))
            game.add_item(Blackjack_btn_double(player))
            if player.same_cards() and len(player.cards) == 2:
                game.add_item(Blackjack_btn_split(player))
            game.add_item(Blackjack_btn_stay(player))

            old_msg = new_msg
            await old_msg.delete()
            new_msg = await channel.send(content=f'Играем с <@{player.id}>', embed=embed, view=game)
            counter = 0
            while counter != 60 and player.calculate_value() < 21 and len(player.cards) < 6:
                if player.action == 'hit':
                    player.action = None
                    counter = 0

                    field = fields[game.players.index(player) + 1]
                    player.cards.append(player.gen_card())
                    field['value'] = 'Ставка: ' + str(player.bet) + '\n' + ' '.join(map(lambda x: x['pic'], player.cards))
                    field['name'] = player.name + ' | ' + str(player.calculate_value())
                    embed = get_embed(embed=embed, fields=fields)
                    if len(game.children) == 4:
                        game.children[2].disabled = True
                    game.children[1].disabled = True
                    await new_msg.edit(embed=embed, view=game)

                elif player.action == 'double':
                    player.action = None
                    money = game.bot.db.get_value('pivo', 'money', 'user_id', player.id)
                    if money < player.bet * 2:
                        await channel.send(f'<@{player.id}>, У тебя не хватает дабаби, чтобы сделать дабл ставку')
                        continue

                    player.bet *= 2
                    field = fields[game.players.index(player) + 1]
                    player.cards.append(player.gen_card())
                    field['value'] = 'Ставка: ' + str(player.bet) + '\n' + ' '.join(map(lambda x: x['pic'], player.cards))
                    field['name'] = player.name + ' | ' + str(player.calculate_value())
                    embed = get_embed(embed=embed, fields=fields)
                    await new_msg.edit(embed=embed, view=None)
                    break
                    
                elif player.action == 'split':
                    player.action = None
                    money = game.bot.db.get_value('pivo', 'money', 'user_id', player.id)
                    if money < player.bet * 2:
                        await channel.send(f'<@{player.id}>, У тебя не хватает дабаби, чтобы сделать сплит.')
                        continue
                    second_hand = Player_bj(player.id, player.name, player.bet)
                    second_hand.deck = deck
                    second_hand.cards = [player.cards[1], second_hand.gen_card()]
                    player.cards = [player.cards[0], player.gen_card()]
                    game.players.insert(game.players.index(player)+1, second_hand)
                    game.children[2].disabled = True

                    field = fields[game.players.index(player) + 1]
                    field['value'] = 'Ставка: ' + str(player.bet) + '\n' + ' '.join(map(lambda x: x['pic'], player.cards))
                    field['name'] = player.name + ' | ' + str(player.calculate_value())

                    cards = ' '.join(map(lambda x: x['pic'], second_hand.cards))
                    new_field = {'name': player.name + ' 2 | ' + str(second_hand.calculate_value()),
                            'value': f'Ставка: {player.bet}\n{cards}',
                            'inline': True}
                    fields.insert(fields.index(field)+1, new_field)

                    embed = get_embed(embed=embed, fields=fields)
                    await new_msg.edit(embed=embed, view=game)

                elif player.action == 'stay':
                    break
                
                else:
                    pass
                counter += 1
                await asyncio.sleep(1)
            if player.calculate_value() > 21:
                await channel.send(f'<@{player.id}>, Ты набрал больше 21 и проиграл!')
            if len(player.cards) == 6:
                await channel.send(f'<@{player.id}>, Нельзя брать больше 6 карт!')

    # Ход диллера
    dealer_field = fields[0]
    dealer_field['value'] = ' '.join(map(lambda x: x['pic'], dealer.cards))
    dealer_field['name'] = 'Дилер | ' + str(dealer.calculate_value())
    embed.description = f'Ход дилера!'
    embed = get_embed(embed=embed, fields=fields)
    await new_msg.edit(content=None, embed=embed, view=None)
    await asyncio.sleep(1)
    while dealer.calculate_value() <= 16 and len(dealer.cards) < 6:
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
    for player in game.players:
        field = fields[game.players.index(player) + 1]
        player_number = player.calculate_value()
        if player_number > 21:
            result = 'Перебор'
            sql += f'update pivo set money = money - {player.bet}, spend = spend + {player.bet} where user_id = {player.id};\n'
            stat_sql += f'update roulette_stat set lose = lose + {player.bet}, lose_count = lose_count+1 where user_id = {player.id};\n'
            trans_sql += f'insert into transactions values ({player.id}, {player.bet}, \'lose bet\', \'\', {mktime(datetime.now().timetuple())});\n'
        else:
            if player_number == 21 and len(player.cards) == 2:
                result = 'Блекджек!'
                sql += f'update pivo set money = money + {player.bet*1.5} where user_id = {player.id};\n'
                stat_sql += f'update roulette_stat set win = win + {player.bet*1.5}, win_count = win_count+1 where user_id = {player.id};\n'
                trans_sql += f'insert into transactions values ({player.id}, {player.bet}, \'win bet\', \'\', {mktime(datetime.now().timetuple())});\n'
            elif player_number > dealer_number or dealer_number > 21:
                result = 'Победа'
                sql += f'update pivo set money = money + {player.bet} where user_id = {player.id};\n'
                stat_sql += f'update roulette_stat set win = win + {player.bet}, win_count = win_count+1 where user_id = {player.id};\n'
                trans_sql += f'insert into transactions values ({player.id}, {player.bet}, \'win bet\', \'\', {mktime(datetime.now().timetuple())});\n'
            elif dealer_number == player_number:
                result = 'Равно'
            else:
                result = 'Мало'
                sql += f'update pivo set money = money - {player.bet}, spend = spend + {player.bet} where user_id = {player.id};\n'
                stat_sql += f'update roulette_stat set lose = lose + {player.bet}, lose_count = lose_count+1 where user_id = {player.id};\n'
                trans_sql += f'insert into transactions values ({player.id}, {player.bet}, \'lose bet\', \'\', {mktime(datetime.now().timetuple())});\n'
        
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
        self.decks[channel_id]['counter'] = 0 


