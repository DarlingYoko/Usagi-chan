import sys, discord, os, subprocess, random, time
from src.functions import isCommand, newLog
from src.guildCommands.createRequest import createRequest
from src.guildCommands.helpCommand import helpCommand
from src.guildCommands.helpValentine import helpValentine
from src.privatCommands.updateShedule import updateShedule
from src.privatCommands.createValentine import valentineCommand
from youtube_dl import YoutubeDL
from gtts import gTTS
from spotdl import __main__ as spotdl
from threading import Thread
from random import randint


def setMessageEvent(self):
    @self.client.event
    async def on_message(message):
        #try:
            if str(message.type) == 'MessageType.pins_add':
                await message.delete()
                return

            if message.author == self.client.user:
                return

            '''
            if message.channel.id == 788546742677143552:
                chtoList = ['что', 'почему', 'как', 'кому', 'зачем', 'кого', '?']

                for chto in chtoList:
                    if chto in message.content.lower():
                        pasvitas = self.client.get_emoji(817877977412665345)
                        await message.add_reaction(pasvitas)
                        continue


                hug = self.client.get_emoji(810217025111719996)
                await message.add_reaction(hug)
            '''


            msg = message.content
            data = {
                    'urlImage': None,
                    'message': message
                    }

            if message.attachments:
                data['urlImage'] = message.attachments[0].url

            if 'cock' in msg.lower() and message.channel.id == 788546742677143552:
                answer = '<:YEP:771044606913151002> COCK'
                await message.channel.send(answer)
                return



            #private messages
            if isCommand(msg, self.config['privateCommands'].values()):
                if str(message.channel.type) == 'private':
                    answer = 'Тебе низя использовать эту команду'
                    '''
                    command = self.config['privateCommands']['createValentine']
                    if msg.startswith(command):
                        data['content'] = msg.split(command)[1]
                        await valentineCommand(self, data = data)
                    '''
                    command = self.config['privateCommands']['updateShedule']
                    if msg.startswith(command) and msg.split()[0] == command:
                        if message.author.id in eval(self.config['sheduleData']['moviegoers']):
                            embeds = updateShedule()
                            channel = await self.client.fetch_channel(self.config['sheduleData']['sheduleChannel'])
                            sheduleEmoji = self.client.get_emoji(810182035955777576)
                            async for messageHistory in channel.history(limit=10):
                                if messageHistory.id == 807711419415396392:
                                    break
                                await messageHistory.delete()
                                self.db.remove(tableName = 'shedule', selector = 'messageId', value = messageHistory.id)

                            for embed in embeds.keys():
                                reloadMes = await channel.send(embed=embed)
                                self.db.insert('shedule', reloadMes.id, embeds[embed], '[]')
                                await reloadMes.add_reaction(sheduleEmoji)

                            answer = 'Успешно!'

                    command = self.config['privateCommands']['simpleMessageCommand']
                    if msg.startswith(command) and msg.split()[0] == command:
                        if message.author.id == self.config['usersIDs'].getint('yokoId'):
                            self.musicPlayer.simpleVoice(msg, command)
                            answer = 'Проговорила'

                    if len(answer) >= 2000:
                        for i in range(0, len(answer), 2000):
                            await message.channel.send(answer[i:i+2000])
                    else:
                        await message.channel.send(answer)





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
                    answer = 'Тебе низя использовать эту команду'
                    delay = 5

                    command = self.config['guildCommands']['createRequest']
                    if msg.startswith(command):
                        data['content'] = msg.split(command)[1]
                        await createRequest(self, data = data)
                        answer = 'Готово'
                        delay = 1

                    command = self.config['guildCommands']['helpCommand']
                    if msg.startswith(command) and msg.split()[0] == command:
                        await helpCommand(self, data = data)
                        answer = 'Готово'
                        delay = 1

                    '''
                    command = self.config['guildCommands']['helpValentine']
                    if msg.startswith(command):
                        await helpValentine(self, data = data)
                    '''
                    command = self.config['guildCommands']['playAudio']
                    if msg.startswith(command) and msg.split()[0] == command:
                        URL = msg.split(command)[1].strip()

                        if message.author.id in eval(self.config['audio']['accessList']):
                            self.musicPlayer.play(URL)
                            answer = 'Добавила песенку в плейлист'


                    command = self.config['guildCommands']['pauseAudio']
                    if msg.startswith(command) and msg.split()[0] == command:
                        if message.author.id in eval(self.config['audio']['accessList']):
                            self.musicPlayer.pauseAudio()
                            answer = 'Поставила на паузу'


                    command = self.config['guildCommands']['resumeAudio']
                    if msg.startswith(command) and msg.split()[0] == command:
                        if message.author.id in eval(self.config['audio']['accessList']):
                            self.musicPlayer.resume()
                            answer = 'Поставила дальше играть'


                    command = self.config['guildCommands']['stopAudio']
                    if msg.startswith(command) and msg.split()[0] == command:
                        if message.author.id in eval(self.config['audio']['accessList']):
                            self.musicPlayer.stop()
                            answer = 'Остановила и очистила'


                    command = self.config['guildCommands']['shuffleAudio']
                    if msg.startswith(command) and msg.split()[0] == command:
                        if message.author.id in eval(self.config['audio']['accessList']):
                            self.musicPlayer.shuffle()
                            answer = 'Перемешала'


                    command = self.config['guildCommands']['nowAudio']
                    if msg.startswith(command) and msg.split()[0] == command:
                        if message.author.id in eval(self.config['audio']['accessList']):
                            answer = self.musicPlayer.nowPlay()


                    command = self.config['guildCommands']['skipAudio']
                    if msg.startswith(command) and msg.split()[0] == command:
                        if message.author.id in eval(self.config['audio']['accessList']):
                            answer = self.musicPlayer.skip()



                    command = self.config['guildCommands']['queryAudio']
                    if msg.startswith(command) and msg.split()[0] == command:
                        answer = self.musicPlayer.query()
                        delay = 60


                    command = self.config['guildCommands']['repeatAudio']
                    if msg.startswith(command) and msg.split()[0] == command:
                        if message.author.id in eval(self.config['audio']['accessList']):
                            answer = self.musicPlayer.repeat(msg)


                    command = self.config['guildCommands']['connectVoice']
                    if msg.startswith(command) and msg.split()[0] == command:
                        if message.author.id == self.config['usersIDs'].getint('yokoId'):
                            await self.musicPlayer.connect(self.client, msg, command)
                            answer = 'Подключилась'

                    if len(answer) >= 2000:
                        for i in range(0, len(answer), 2000):
                            await message.channel.send(answer[i:i+2000], delete_after = delay)
                    else:
                        await message.channel.send(answer, delete_after = delay)


                else:
                    await message.channel.send('<@{0}>, эта команда только для каналов'.format(UID), delete_after = 5)


        #except Exception as e:
            #exc_type, exc_obj, exc_tb = sys.exc_info()
            #newLog(exc_type, exc_obj, exc_tb, e)
