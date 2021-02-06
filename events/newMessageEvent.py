from src.functions import isCommand, newLog
from src.guildCommands.createRequest import createRequest
from src.guildCommands.helpCommand import helpCommand
import sys

def setMessageEvent(self):
    @self.client.event
    async def on_message(message):
        try:
            if str(message.type) == 'MessageType.pins_add':
                await message.delete()
                return

            if message.author == self.client.user:
                return

            msg = message.content
            data = {
                    'attachmentURL': None,
                    'message': message
                    }

            if message.attachments:
                data['urlImage'] = message.attachments[0].url

            #private messages
            if isCommand(msg, self.config['privateCommands'].values()):
                if str(message.channel.type) == 'private':
                    '''
                    splitStr = privateCommands['createValentine']
                    if msg.startswith(splitStr):
                        data['content'] = msg.split(splitStr)[1]
                        await valentineCommand(data = data, members = members)

                    splitStr = privateCommands['deleteValentine']
                    if msg.startswith(splitStr):
                        data['content'] = msg.split(splitStr)[1]
                        await deleteValentine(data = data)
                    '''
                    command = self.config['privateCommands']['simpleMessageCommand']
                    if msg.startswith(command):
                        if message.author.id == self.config['usersIDs']['yokoId']:
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

                else:
                    await message.channel.send('<@{0}>, эта команда только для каналов'.format(UID), delete_after = 5)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            newLog(exc_type, exc_obj, exc_tb, e)
