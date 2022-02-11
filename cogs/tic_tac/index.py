import discord, requests, asyncio, random
from discord.ext import commands, tasks
from bin.converters import *
from discord import Button
from random import choice
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
            content = f'Сейчас ход {view.player_2.name}'
        elif view.current_player == view.O:# and interaction.user.id == view.player_2.id:
            self.style = discord.ButtonStyle.success
            self.label = "O"
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = f'Сейчас ход {view.player_1.name}'

        else:
            return await interaction.response.send_message(content='Ты не ходишь сейчас!', ephemeral=True)

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                content = "X won!"
                view.winner = view.player_1.name
            elif winner == view.O:
                content = "O won!"
                view.winner = view.player_2.name
            else:
                content = "It's a tie!"
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
        game_counter = 1
        result = {}
        games_name = {1: 'Первая', 2: 'Вторая', 3: 'Третья', 4: 'Четвёртая', 5: 'Пятая', 6: 'Шестая', 7: 'Седьмая', }
        rounds_name = {1: 'первый', 2: 'второй', 3: 'третий', 4: 'четвёртый', 5: 'пятый'}
        for game in self.bot.table:
            player_1 = await ctx.bot.fetch_user(game[0])
            player_2 = await ctx.bot.fetch_user(game[1])
            game_name = games_name[game_counter]
            await ctx.send(f'{game_name} игра между {player_1.name} и {player_2.name}')
            for i in range(1, 4):
                round = rounds_name[i]
                await ctx.send(f'Рануд {round}')
                players = [player_1, player_2]
                player_1 = choice(players)
                players.remove(player_1)
                player_2 = players[0]
                game_table = TicTacToe(player_1, player_2)
                await ctx.send(f'Первым ходит {player_1.name} -- **Х**', view=game_table)

                result_game = await game_table.wait()
                if not result_game:
                    text = 'Ничья!'
                    if game_table.winner:
                        text = f'Игра закончилась успешно, победитель - {game_table.winner}'
                        if game_table.winner in result.keys():
                            result[game_table.winner] += 1
                        else:
                            result[game_table.winner] = 1
                    await ctx.send(text)
                else:
                    await ctx.send(f'Игра завершилась раньше времени, хотите повторить?')

            game_counter += 1
        await ctx.send(f'Результаты турнира - {result}')



    @commands.command(aliases = ['регистрация'])
    @commands.is_owner()
    async def reg(self, ctx, name: str):
        self.bot.players.append(name)
        await ctx.send('Записала тебя!')

    @commands.command(name = 'игроки')
    @commands.is_owner()
    async def players(self, ctx):
        await ctx.send(self.bot.players)


    @commands.command(aliases = ['таблица'])
    @commands.is_owner()
    async def table(self, ctx):
        table = []
        players_copy = self.bot.players.copy()
        for player in self.bot.players:
            if check_players(player, table):
                continue
            if len(players_copy) == 1:
                table.append([player])
                break
            players_copy.remove(player)
            sec_player = choice(players_copy)
            table.append([player, sec_player])
            players_copy.remove(sec_player)

        self.bot.table = table
        await ctx.send(table)

    @commands.command()
    @commands.is_owner()
    async def show_table(self, ctx):
        if not self.bot.table:
            return await ctx.send('Таблица ещё не была создана!')

        answer = 'Раунд N\n'
        for game in self.bot.table:
            player_1 = await ctx.bot.fetch_user(game[0])
            player_2 = await ctx.bot.fetch_user(game[1])
            answer += f'{player_1.name} + {player_2.name}\n'
        await ctx.send(answer)

    @commands.command()
    @commands.is_owner()
    async def messages(self, ctx):
        guild = await ctx.bot.fetch_guild(858053936313008129)
        channels = await guild.fetch_channels()
        data = {}
        users = {}
        emojis = {}
        for channel in channels:
            if str(channel.type) == 'text':
                print(f'обрабатываю {channel}')
                async for message in channel.history(limit=None):
                    if message.author.name in users.keys():
                        users[message.author.name] += 1
                    else:
                        users[message.author.name] = 1

                    for word in message.content.split(' '):
                        if word.startswith('<:') and word.endswith('>'):
                            if word in emojis.keys():
                                emojis[word] += 1
                            else:
                                emojis[word] = 1
                        else:
                            if word in data.keys():
                                data[word] += 1
                            else:
                                data[word] = 1

        users = {k: v for k, v in sorted(users.items(), key=lambda item: item[1], reverse=True)}
        users = list(users.items())[:20]
        data = {k: v for k, v in sorted(data.items(), key=lambda item: item[1], reverse=True)}
        data = list(data.items())[:40]
        emojis = {k: v for k, v in sorted(emojis.items(), key=lambda item: item[1], reverse=True)}
        emojis = list(emojis.items())[:20]
        users = f'Топ кол-ва сообщений {users}'
        messages = f'Топ слов {data}'
        emojis = f'Топ эмоджиков{emojis}'

        if len(users) >= 2000:
            for i in range(0, len(users), 2000):
                await ctx.send(users[i:i+2000])
        else:
            await ctx.send(users)

        if len(messages) >= 2000:
            for i in range(0, len(messages), 2000):
                await ctx.send(messages[i:i+2000])
        else:
            await ctx.send(messages)

        if len(emojis) >= 2000:
            for i in range(0, len(emojis), 2000):
                await ctx.send(emojis[i:i+2000])
        else:
            await ctx.send(emojis)











def setup(bot):
    bot.add_cog(Tic_tac_toe(bot))
