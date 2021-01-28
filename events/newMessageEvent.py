from src.functions import isCommand
import src.config as config
from src.guildCommads.createRequest import createRequest

def setMessageEvent(self):
    @self.client.event
    async def on_message(message):

        if str(message.type) == 'MessageType.pins_add':
            await message.delete()
            return

        if message.author == self.client.user:
            return
        if message.guild.id == 346775939105161247:
            return

        msg = message.content
        data = {'client': self.client,
                'attachmentURL': None,
                'message': message}

        if message.attachments:
            data['urlImage'] = message.attachments[0].url

        #private messages
        '''
        if isCommand(msg, privateCommands.values()):
            if str(message.channel.type) == 'private':

                splitStr = privateCommands['createValentine']
                if msg.startswith(splitStr):
                    data['content'] = msg.split(splitStr)[1]
                    await valentineCommand(data = data, members = members)

                splitStr = privateCommands['deleteValentine']
                if msg.startswith(splitStr):
                    data['content'] = msg.split(splitStr)[1]
                    await deleteValentine(data = data)

                if msg.startswith(privateCommands['simpleMessageCommand']):
                    if UID == config.yokoId:
                        logChannel = client.get_channel(346775939709009920)
                        logChannel.send(msg.split(simpleMessageCommand)[1])
                    else:
                        await message.channel.send('Ты не мой создатель!')

            # channel messages
            else:
                timeMsg = await message.channel.send('<@{0}>, эта команда только для личных сообщений'.format(UID))
                await message.delete()
                await timeMsg.delete(delay = 3)
                #pass
            return
        '''
        if isCommand(msg, config.guildCommands.values()):
            await message.delete()
            if str(message.channel.type) == 'text':

                command = config.guildCommands['createRequest']
                if msg.startswith(command):
                    data['content'] = msg.split(command)[1]
                    await createRequest(data = data, db = self.db)
                    print('Create')

                command = config.guildCommands['helpCommand']
                if msg.startswith(command):
                    #await helpCommand(data = data)
                    print('Help')




            else:
                await message.channel.send('<@{0}>, эта команда только для каналов'.format(UID), delete_after = 5)
