from importlib.resources import contents
import discord, requests, asyncio, random
from discord.ext import commands, tasks
from bin.converters import *
from discord import Button
from random import choice, randint
from typing import List
from .utils import check_players


# турнир:
# 1. игроки регистрируются через команду +
# 2. Усаги собирает всех и генирирует турнирную сетку -> присылает в чатик +
#
# игра:
# 1. Все игры поочереди и есть список очерёдности
# 2. Есть роль, которая может писать в этом канале и Усаги выдаёт тем, кто сейчас играет
# 3. игры бо3 финал бо5
# 4. Время на подумать 5 минут у каждого игрока на игру.
# 5. Игровое поле представляет собой просто кнопки.
#
# результаты:
# после каждой игры подводятся результаты и записываются в табличку

# 1. первый +1 
# 2. второй +1
# 3. ничья +0

# Defines a custom button that contains the logic of the game.
# The ['TicTacToe'] bit is for type hinting purposes to tell your IDE or linter
# what the type of `self.view` is. It is not required.
class TicTacToeButton(discord.ui.Button["TicTacToe"]):
    def __init__(self, x: int, y: int):
        # A label is required, but we don't need one so a zero-width space is used
        # The row parameter tells the View which row to place the button under.
        # A View can only contain up to 5 rows -- each row can only have 5 buttons.
        # Since a Tic Tac Toe grid is 3x3 that means we have 3 rows and 3 columns.
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    # This function is called whenever this particular button is pressed
    # This is part of the "meat" of the game logic
    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToe = self.view
        state = view.board[self.y][self.x]
        if state in (view.X, view.O):
            return

        if view.current_player == view.X:# and interaction.user.id == view.player_1.id:
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = f'Сейчас ход {view.player_2.name} ― 🟢'
        elif view.current_player == view.O:# and interaction.user.id == view.player_2.id:
            self.style = discord.ButtonStyle.success
            self.label = "O"
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = f'Сейчас ход {view.player_1.name} ― ❌'

        else:
            return await interaction.response.send_message(content='Ты не ходишь сейчас!', ephemeral=True)

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                content = f'```diff\n- Победитель этой игры - {view.player_1.name} -\n```'
                view.winner = view.player_1
            elif winner == view.O:
                content = f'```diff\n+ Победитель этой игры - {view.player_2.name} +\n```'
                view.winner = view.player_2
            else:
                content = f'```diff\n--- В этой игре нет победителя\n```'
                view.winner = ''

            for child in view.children:
                child.disabled = True

            view.stop()

        await interaction.response.edit_message(content=content, view=view)


# This is our actual board View
class TicTacToe(discord.ui.View):
    # This tells the IDE or linter that all our children will be TicTacToeButtons
    # This is not required
    children: List[TicTacToeButton]
    X = -1
    O = 1
    Tie = 2

    def __init__(self, player_1, player_2):
        super().__init__()
        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        self.player_1 = player_1
        self.player_2 = player_2
        self.winner = None


        # Our board is made up of 3 by 3 TicTacToeButtons
        # The TicTacToeButton maintains the callbacks and helps steer
        # the actual game.
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    # This method checks for the board winner -- it is used by the TicTacToeButton
    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check vertical
        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check diagonals
        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        # If we're here, we need to check if a tie was made
        if all(i != 0 for row in self.board for i in row):
            return self.Tie

        return None

class Tic_tac_toe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config


    @commands.command()
    @commands.is_owner()
    async def game(self, ctx):
        
        tournament_result = {}
        games_name = {1: 'Первая', 2: 'Вторая', 3: 'Третья', 4: 'Четвёртая', 5: 'Пятая', 6: 'Шестая', 7: 'Седьмая', }
        rounds_name = {1: 'первый', 2: 'второй', 3: 'третий', 4: 'четвёртый', 5: 'пятый'}
        table = self.gen_table(self.bot.players) # get players from DB
        game_counter = 1
        print(table)
        await ctx.send('Начинаем наш турнир по крестикам-ноликам! Юююхууу!!\nИ перед вашими глазами турнирная таблица на сегодняшний вечер:')
        while table:
            view_table = '```cs\n# ――――――――――\n'
            counter = 1
            for game in table:
                player_1 = await ctx.bot.fetch_user(game[0])
                if game[1] != None:
                    player_2 = await ctx.bot.fetch_user(game[1])
                    view_table += f'{counter}. {player_1.name} "VS" {player_2.name}\n# ――――――――――\n'
                else:
                    view_table += f'{counter}. {player_1.name} "VS" Нет противника\n# ――――――――――\n'
                counter += 1
            view_table += '```'
            await ctx.send(content=view_table)
            
            new_players = []
            
            for game in table:
                player_1 = await ctx.bot.fetch_user(game[0])
                if game[1] == None:
                    await ctx.send(f'Игрок **{player_1.name}** проходит в следующий тур, тк нет противника!.')
                    new_players.append(player_1.id)
                    # tournament_result[player_1.id] += 2
                    continue
                player_2 = await ctx.bot.fetch_user(game[1])
                if player_1.id not in tournament_result.keys():
                    tournament_result[player_1.id] = 0
                if player_2.id not in tournament_result.keys():
                    tournament_result[player_2.id] = 0
                    if game_counter < 5:
                        game_name = games_name[game_counter]
                    else:
                        game_name = 'Хуй знает какая'

                result = {player_1.id: 0, player_2.id: 0}
                await ctx.send(f'**{game_name} игра**```prolog\n"{player_1.name}" VS "{player_2.name}"\n```')
                res_1, res_2 = 0, 0
                round_counter = 1
                while abs(res_1 - res_2) != 2:
                    if round_counter < 5:
                        round = rounds_name[round_counter]
                    else:
                        round = 'Хуй знает какой'
                    await ctx.send(f'**Раунд - {round}**')
                    if randint(0, 1):
                        player_1, player_2 = player_2, player_1

                    game_table = TicTacToe(player_1, player_2)
                    await ctx.send(f'Первым ходит {player_1.name} ― ❌', view=game_table)

                    result_game = await game_table.wait()
                    if not result_game and game_table.winner:
                        result[game_table.winner.id] += 1

                    res_1 = result[player_1.id]
                    res_2 = result[player_2.id]
                    round_counter += 1
                if res_1 > res_2:
                    new_players.append(player_1.id)
                else:
                    new_players.append(player_2.id)

                for key, item in result.items():
                    # print(tournament_result, key, item)
                    tournament_result[key] += item
                game_counter += 1
            print(new_players)
            if len(new_players) == 1:
                await ctx.send(f'Турнир окончен, победитель - <@{new_players[0]}>')
                break
            table = self.gen_table(new_players)

        winner = await ctx.bot.fetch_user(new_players[0])
        results = f'```cs\n# Полные результаты турнира:\n1. {winner.name} - {tournament_result[new_players[0]]} Очков\n'
        del tournament_result[new_players[0]]
        winners = {k: v for k, v in sorted(tournament_result.items(), key=lambda item: item[1], reverse=True)}
        counter = 2
        for key, item in winners.items():
            winner = await ctx.bot.fetch_user(key)
            results += f'{counter}. {winner.name} - {item} Очков\n'
            counter += 1
        results += '```'
        await ctx.send(content=results)



    @commands.command(aliases = ['регистрация'])
    # @commands.is_owner()
    async def reg(self, ctx):
        text = 'Не удалось записать тебя на турнир, попробуй позже'
        append_result = self.bot.db.insert('tictac', ctx.message.author.id, 'type')
        # print(append_result)
        if append_result:
            text = 'Записала тебя!'
        await ctx.send(content=text)

    @commands.command(aliases = ['выйти'])
    # @commands.is_owner()
    async def quit_reg(self, ctx):
        text = 'Не удалось удалить тебя, попробуй позже'
        remove_result = self.bot.db.remove('tictac', 'user_id', ctx.message.author.id)
        # print(remove_result)
        if remove_result:
            text = 'Удалила тебя!'
        await ctx.send(content=text)

    @commands.command(name = 'игроки')
    async def players(self, ctx):
        players = self.bot.db.get_all('tictac')
        text = '```cs\n# Сейчас записаны следующие люди:\n'
        counter = 1
        for player in players:
            player = await ctx.bot.fetch_user(player[0])
            text += f'{counter}. {player.name}\n'
            counter += 1
        text += '```'
        await ctx.send(text)


    def gen_table(self, players: list) -> list[int]:
        table = []
        for player in players:
            # print(players)
            if check_players(player, table):
                continue

            players.remove(player)
            sec_player = choice(players)
            table.append([player, sec_player])
            players.remove(sec_player)
        if len(players) == 1:
            table.append([players[-1], None])
        return table


    # @commands.command()
    # @commands.is_owner()
    # async def messages(self, ctx, channel_id: int):
    #     guild = await ctx.bot.fetch_guild(858053936313008129)
    #     channel = await guild.fetch_channel(channel_id)
    #     data = {}
    #     users = {}
    #     emojis = {}
    #     print(f'обрабатываю {channel}')
    #     async for message in channel.history(limit=None):
    #     # messages = await channel.history(limit=None).flatten()
    #     # print(len(messages))
    #     # for message in messages:
    #         if message.author.bot: 
    #             continue
    #         if message.author.name in users.keys():
    #             users[message.author.name] += 1
    #         else:
    #             users[message.author.name] = 1

            # for word in message.content.split(' '):
            #     if word.startswith('<:') and word.endswith('>'):
            #         if word in emojis.keys():
            #             emojis[word] += 1
            #         else:
            #             emojis[word] = 1
            #     else:
            #         if word in data.keys():
            #             data[word] += 1
            #         else:
            #             data[word] = 1

        # users = {k: v for k, v in sorted(users.items(), key=lambda item: item[1], reverse=False)}
        # users = list(users.items())
        # users = f'Топ кол-ва сообщений {users}'
        

        # if len(users) >= 2000:
        #     for i in range(0, len(users), 2000):
        #         await ctx.send(users[i:i+2000])
        # else:
        #     await ctx.send(users)









def setup(bot):
    bot.add_cog(Tic_tac_toe(bot))
