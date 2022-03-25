from discord.ext import commands
from time import mktime
from datetime import datetime
from bin.functions import get_embed, format_time
from cogs.casino.bj import *
from cogs.casino.roulette import *



class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.roulettes = []
        self.blackjack_games = []
        self.ready_game = True
        # self.roulette_counter.start()
        # self.blackjack_counter.start()
        self.RED = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        self.BLACK = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
        self.columns = {1: range(1, 36, 3), 2: range(2, 36, 3), 3: range(3, 37, 3)}
        self.dozens = {1: range(1, 13), 2: range(13, 25), 3: range(25, 37)}
        self.decks = {956266610669285376: {'deck': None, 'counter': 0}, 
            956266663681081434: {'deck': None, 'counter': 0}, 
            807349536321175582: {'deck': None, 'counter': 0}} 
    

    @commands.cooldown(per=60, rate=1)
    @commands.command(name='рулетка', aliases=['roulette'])
    async def roulette(self, ctx):
        if ctx.channel.id not in [951927512445886584, 951927724849635358, 807349536321175582]:
            return await ctx.channel.send(f'{ctx.author.mention}, здесь нельзя играть в рулетку <a:Tssk:883736146578915338>. Тебе сюда -> <#951927512445886584> <#951927724849635358>')
        if not self.ready_game:
            return await ctx.send(f'{ctx.author.mention}, Сейчас нельзя создавать игры, я обновляюсь!')

        roulette_game = Roulette_view(ctx.bot)

        timer = int(mktime(datetime.now().timetuple()) + 60*2+20)
        image_url = 'https://media.discordapp.net/attachments/807349536321175582/951940401852452944/roulette-table-vector-20671332.png'
        embed = get_embed(title='Новая рулетка!', 
            description=f'Старт <t:{timer}:R>\nСкорее делайте ваши ставочки!',
            url_image=image_url)
        
        message = await ctx.send(embed=embed, view=roulette_game)
        data = {'message': message, 'embed': embed, 'game': roulette_game}
        await ctx.message.delete()
        await roulette_game.start_game(self, data)

    # @tasks.loop(seconds=1)
    # async def roulette_counter(self):
    #     remove = []
    #     for message in self.roulettes:
    #         message['timer'] -= 1
    #         if message['timer'] == 0:
                
    #             remove.append(message)
    #     for msg in remove:
    #         self.roulettes.remove(msg)

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
        if ctx.channel.id not in [956266610669285376, 956266663681081434, 807349536321175582]:
            return await ctx.channel.send(f'{ctx.author.mention}, здесь нельзя играть в блекджек <a:Tssk:883736146578915338>. Тебе сюда -> <#956266610669285376> <#956266663681081434>')
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
        data ={'message': message, 'embed': embed, 'game': blackjack_game}
        await ctx.message.delete()
        await blackjack_game.start_game(self, data)

    @blackjack.error
    async def blackjack_errors(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            time = format_time(retry_after)
            await ctx.send(f'{ctx.author.mention}, Рановато для нового стола блекджека, подожди пока закончится предыдущий! Попробуй через {time}')

    # @tasks.loop(seconds=1)
    # async def blackjack_counter(self):
    #     for message in self.blackjack_games:
    #         message['timer'] -= 1
    #         if message['timer'] == 0:
    #             pass
                # print(11111)
                # await asyncio.sleep(10)
                # Thread(target = asyncio.run, args=(, )).start()
                




        

        



        


def setup(bot):
    bot.add_cog(Casino(bot))