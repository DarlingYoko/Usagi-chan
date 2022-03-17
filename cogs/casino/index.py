from discord.ext import commands, tasks
from discord import File, SelectOption
from time import mktime
from datetime import datetime
from discord.ui import Modal, Select, InputText
from bin.functions import get_embed, format_time
from random import SystemRandom, randint
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

    


        


class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.roulettes = []
        self.ready_game = True
        self.roulette_counter.start()
        self.RED = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        self.BLACK = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]

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
                            (type_bet == 'black' and result in self.BLACK):
                            
                            winners += f'{name}, поставил {bet}<:dababy:949712395385843782> на {type_bet} {text}'

                            if type_bet in ['even', 'odd', 'red', 'black']:
                                bet *= 2
                            else:
                                bet *= 36
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
                    'value': text_money,
                    'inline': True},
                {'name': '_ _', 
                    'value': '_ _',
                    'inline': True},
                {'name': 'Топ лакеров', 
                    'value': text_spend,
                    'inline': True},
                {'name': 'Топ транжир', 
                    'value': text_spend_for_self,
                    'inline': True},
                {'name': '_ _', 
                    'value': '_ _',
                    'inline': True},
                {'name': 'Топ лузеров', 
                    'value': text_spend_for_user,
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

        

        



        


def setup(bot):
    bot.add_cog(Casino(bot))