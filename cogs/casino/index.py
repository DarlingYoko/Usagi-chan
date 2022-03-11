from discord.ext import commands, tasks
from discord import File, SelectOption
from time import mktime
from datetime import datetime
from discord.ui import Modal, Select, InputText
from bin.functions import get_embed, format_time
from random import randint
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
           self.add_item(InputText(label='Число, на которое ты хочешь поставить', value=1, custom_id='own_bet')) 
        self.add_item(InputText(label='Ставка', value=1, custom_id='bet_count'))
        
    async def callback(self, interaction: discord.Interaction):

        if self.game.is_finished():
            return await interaction.response.send_message(content=f'Ты не успел поставить(', ephemeral=True)

        own_bet = None
        if self.children[0].custom_id == 'own_bet':
            own_bet = self.children[0].value
            if not own_bet.isdecimal():
                return await interaction.response.send_message(content=f'Ты ввёл не число, в поле выбора числа!', ephemeral=True)
            own_bet = int(own_bet)
            if own_bet < 1 or own_bet > 36:
                return await interaction.response.send_message(content=f'Ты ввёл недопустимое число, в поле выбора числа!', ephemeral=True)
            bet = self.children[1].value
        else:
            bet = self.children[0].value
        
        if not bet.isdecimal():
            return await interaction.response.send_message(content=f'Ты ввёл не число, в своей ставки!', ephemeral=True)
        bet = int(bet)
        values = self.game.bot.db.custom_command(f'SELECT money, spend from pivo where user_id = {interaction.user.id};')
        if not values:
            return await interaction.response.send_message(content=f'У тебя нет <:dababy:949712395385843782> в банке!', ephemeral=True)

        values = values[0]
        money, spend = values[0], values[1]
        if bet > money:
            return await interaction.response.send_message(content=f'Ты не можешь сделать ставку больше чем у тебя есть <:dababy:949712395385843782>!', ephemeral=True)
        # print(self.children[1].value, self.children[1].custom_id)
        money -= bet
        spend += bet
        self.game.bot.db.custom_command(f'UPDATE pivo set money = {money}, spend = {spend} where user_id = {interaction.user.id};')
        self.game.players[interaction.user.id] = {'type_bet': self.bet, 'bet': bet, 'own_bet': own_bet, 'money': money, 'name': interaction.user.name}
        await interaction.response.send_message(content=f'Ты сделал ставку в размере {bet} <:dababy:949712395385843782> на {self.bet}', ephemeral=True)

class Roulette_bet_select(Select['Roulette_view']):
    def __init__(self):
        options = [
            SelectOption(label='Красное', value='red'),
            SelectOption(label='Чёрное', value='black'),
            SelectOption(label='Зеро', value='zero'),
            SelectOption(label='Чётное', value='even'),
            SelectOption(label='Нечётное', value='odd'),
            SelectOption(label='хуй', value='hui'),
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
        self.roulette_counter.start()
        self.RED = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]

    @commands.cooldown(per=60*5+30, rate=1, type=commands.BucketType.channel)
    @commands.command(name='рулетка', aliases=['roulette'])
    async def roulette(self, ctx):
        roulette_game = Roulette_view(ctx.bot)


        timer = int(mktime(datetime.now().timetuple()) + 60*5)
        image_url = 'https://media.discordapp.net/attachments/807349536321175582/951940401852452944/roulette-table-vector-20671332.png'
        embed = get_embed(title='Новая рулетка!', 
            description=f'Старт <t:{timer}:R>\nСкорее делайте ваши ставочки!',
            url_image=image_url)
        
        message = await ctx.send(embed=embed, view=roulette_game)
        self.roulettes.append({'message': message, 'embed': embed, 'game': roulette_game, 'timer': 60})
        await ctx.message.delete()

    @tasks.loop(seconds=1)
    async def roulette_counter(self):
        for message in self.roulettes:
            message['timer'] -= 1
            if message['timer'] == 0:
                message['game'].stop()
                result = randint(0, 36)
                winners = 'Победители:\n'
                losers = 'Проигравшие:\n'
                for player_id, data in message['game'].players.items():
                    type_bet = data['type_bet']
                    bet = data['bet']
                    own_bet = data['own_bet']
                    money = data['money']
                    name = data['name']
                    if own_bet:
                        text = f'на число {own_bet}\n'
                    else:
                        text = '\n'

                    if (type_bet == 'even' and result % 2 == 0) or \
                        (type_bet == 'odd' and result % 2 == 1) or \
                        (type_bet == 'zero' and result == 0) or \
                        (type_bet == 'own' and result == own_bet) or \
                        (type_bet == 'red' and result in self.RED) or \
                        (type_bet == 'black' and result not in self.RED):
                        
                        winners += f'{name}, поставил {bet}<:dababy:949712395385843782> на {type_bet} {text}'
                        money = self.bot.db.get_value('pivo', 'money', 'user_id', player_id)
                        if type_bet in ['even', 'odd', 'red', 'black']:
                            self.bot.db.update('pivo', 'money', 'user_id', money + bet*2, player_id)
                        else:
                            self.bot.db.update('pivo', 'money', 'user_id', money + bet*36, player_id)
                    else:
                        losers += f'{name}, поставил {bet}<:dababy:949712395385843782> на {type_bet} {text}'
                        


                gif_url = 'https://media.discordapp.net/attachments/807349536321175582/951805421050544138/1VNB.gif'
                embed = get_embed(embed=message['embed'],
                    description='Все ставки приняты, больше ставки не принимаются!\nКрутим рулетку!',
                    url_image=gif_url)
                await message['message'].edit(embed=embed, view=None)

                await asyncio.sleep(10)
                final_url = 'https://media.discordapp.net/attachments/807349536321175582/951946592968130561/3.png'
                embed = get_embed(embed=embed,
                    title='Рулетка закончена',
                    description=f'Выпало {result}!\n{winners}\n\n{losers}',
                    url_image=final_url)
                await message['message'].edit(embed=embed)

    @roulette.error
    async def roulette_errors(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            time = format_time(retry_after)
            await ctx.send(f'{ctx.author.mention}, Рановато для новой рулетки, подожди пока закончится предыдущая! Попробуй через {time}')



        


def setup(bot):
    bot.add_cog(Casino(bot))