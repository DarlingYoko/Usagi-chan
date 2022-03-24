CARDS = {'2': ['<:01:955875487002005554>', '<:14:955875487140433960>', '<:27:955875486687428661>', '<:40:955875486913945692>'], 
            '3': ['<:02:955875486964260944>', '<:15:955875487153000468>', '<:28:955875486783926293>', '<:41:955892980617728010>'], 
            '4': ['<:03:955875486985252974>', '<:16:955875487228506173>', '<:29:955875486754537523>', '<:42:955875486972641281>'], 
            '5': ['<:04:955875486951682168>', '<:17:955875487165599844>', '<:30:955875487098482778>', '<:43:955875486922338335> '], 
            '6': ['<:05:955875486968459284>', '<:18:955875487035568178>', '<:31:955875487203356783>', '<:44:955875487283019846>'], 
            '7': ['<:06:955875487039770754>', '<:19:955875487253680190>', '<:32:955875486830034945>', '<:45:955875487375298601>'], 
            '8': ['<:07:955875487027175484>', '<:20:955875487127851058>', '<:33:955875487236911114>', '<:46:955875487354322964>'], 
            '9': ['<:08:955875486846812251>', '<:21:955875487106883614>', '<:34:955875487354331206>', '<:47:955875487236915210> '], 
            '10': ['<:09:955875487136231485>', '<:22:955875487085908028>', '<:35:955875487203328050>', '<:48:955875487194947665>'],  
            'jack': ['<:10:955875487199154276>', '<:23:955875486934892545>', '<:36:955891579929911326>', '<:49:955893071550238771>'], 
            'queen': ['<:11:955875487123644477>', '<:24:955875486804893710>', '<:37:955875487207534612>', '<:50:955893134418649178>'], 
            'king': ['<:12:955875486679072850>', '<:25:955875487048163329>', '<:38:955875487010418729>', '<:51:955887623807844502>'], 
            'ace': ['<:00:955880097989156947>', '<:13:955875486997835867>', '<:26:955875487224311978>', '<:39:955875487027171439>']}

from random import SystemRandom, choice

class Player_bj:
    def __init__(self): 
        self.cards = [self.gen_card(), self.gen_card()]
    
    def calculate_value(self, slice = None):
        value = 0
        for card in self.cards[:slice]:
            card = card['id']
            if card.isdecimal():
                value += int(card)
            elif card in ['jack', 'queen', 'king']:
                value += 10
            elif card == 'ace':
                ace = 0
                for card in self.cards:
                    if card['id'] == 'ace':
                        ace += 1
                if ace >= 2:
                    value += 1
                else:
                    value += 11

            else:
                pass
        return value

    def gen_card(self):
        rng = SystemRandom()
        cards_list = list(CARDS.keys())
        len_cards = len(cards_list) - 1
        card = cards_list[rng.randint(0, len_cards)]
        pic = choice(CARDS[card])
        return {'id': card, 'pic': pic}

    