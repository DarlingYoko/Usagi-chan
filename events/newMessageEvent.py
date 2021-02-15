from src.functions import isCommand, newLog
from src.guildCommands.createRequest import createRequest
from src.guildCommands.helpCommand import helpCommand
from src.guildCommands.helpValentine import helpValentine
from src.privatCommands.updateShedule import updateShedule
from src.privatCommands.createValentine import valentineCommand
import sys

def setMessageEvent(self):
    @self.client.event
    async def on_message(message):
        #try:
            if str(message.type) == 'MessageType.pins_add':
                await message.delete()
                return

            if message.author == self.client.user:
                return

            msg = message.content
            data = {
                    'urlImage': None,
                    'message': message
                    }

            if message.attachments:
                data['urlImage'] = message.attachments[0].url

            #private messages
            if isCommand(msg, self.config['privateCommands'].values()):
                if str(message.channel.type) == 'private':

                    command = self.config['privateCommands']['createValentine']
                    if msg.startswith(command):
                        data['content'] = msg.split(command)[1]
                        await valentineCommand(self, data = data)

                    command = self.config['privateCommands']['updateShedule']
                    if msg.startswith(command):
                        if message.author.id in eval(self.config['sheduleData']['moviegoers']):
                            embed = updateShedule()
                            await message.channel.send('Успешно!')
                            channel = await self.client.fetch_channel(self.config['sheduleData']['sheduleChannel'])
                            msg = await channel.fetch_message(self.config['sheduleData']['sheduleId'])
                            await msg.edit(embed=embed)
                        else:
                            await message.channel.send('У вас нет прав на использование этой команды.')


                    command = self.config['privateCommands']['simpleMessageCommand']
                    if msg.startswith(command):
                        if message.author.id == self.config['usersIDs'].getint('yokoId'):
                            channel = self.client.get_channel(346775939709009920)
                            await channel.send(msg.split(command)[1])
                        else:
                            await message.channel.send('Ты не мой создатель!')

                # channel messages
                else:
                    timeMsg = await message.channel.send('<@{0}>, эта команда только для личных сообщений'.format(UID))
                    await message.delete()
                    await timeMsg.delete(delay = 3)
                    #pass
                return


            if isCommand(msg, self.config['guildCommands'].values()):
                await message.delete()
                if str(message.channel.type) == 'text':

                    command = self.config['guildCommands']['createRequest']
                    if msg.startswith(command):
                        data['content'] = msg.split(command)[1]
                        await createRequest(self, data = data)

                    command = self.config['guildCommands']['helpCommand']
                    if msg.startswith(command):
                        await helpCommand(self, data = data)

                    command = self.config['guildCommands']['helpValentine']
                    if msg.startswith(command):
                        await helpValentine(self, data = data)

                else:
                    await message.channel.send('<@{0}>, эта команда только для каналов'.format(UID), delete_after = 5)

        #except Exception as e:
            #exc_type, exc_obj, exc_tb = sys.exc_info()
            #newLog(exc_type, exc_obj, exc_tb, e)
