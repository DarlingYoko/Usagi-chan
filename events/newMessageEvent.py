import sys, discord, os, subprocess, random, time, asyncio
from src.functions import isCommand, newLog
from bin.guildCommands.createRequest import createRequest
from bin.guildCommands.helpCommand import helpCommand
from bin.guildCommands.helpValentine import helpValentine
from bin.guildCommands.boostPot import boostPot
from bin.guildCommands.manualRemoveRequest import manualRemoveRequest
from bin.guildCommands.checkHistory import checkHistory
from bin.guildCommands.role import createNewRole
from bin.guildCommands.addEmoji import createNewEmoji
from bin.guildCommands.predictions import predict
from bin.guildCommands.purge import purge
from bin.privatCommands.updateShedule import updateShedule, removeSession
from bin.privatCommands.createValentine import valentineCommand
from bin.commandConfig import commands, texts
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


            guild = await self.client.fetch_guild(self.config['data']['guildId'])
            emojis = {858655225412845568: 859363980228427776, 858727806401904660: 858179418371784714}
            if message.channel.id in emojis.keys() and message.attachments:
                emoji = self.client.get_emoji(emojis[message.channel.id])
                await message.add_reaction(emoji)

            msg = message.content


            if (message.channel.id == self.config['data'].getint('frameChannel') or
            message.channel.id == self.config['data'].getint('simpChannel') or
            message.channel.id == self.config['data'].getint('stoikaChannel') or
            message.channel.id == self.config['data'].getint('usualChannelId')):
                for key in texts.keys():
                    if key in msg.lower():
                        await message.channel.send(texts[key])


            try:
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
                        if msg.split()[0].lower() == command:
                            if message.author.id in eval(self.config['sheduleData']['moviegoers']):
                                embeds = updateShedule()
                                channel = await self.client.fetch_channel(self.config['sheduleData']['sheduleChannel'])
                                sheduleEmoji = self.client.get_emoji(810182035955777576)
                                for embed in embeds.keys():
                                    reloadMes = await channel.send(embed=embed)
                                    self.db.insert('shedule', reloadMes.id, embeds[embed], '[]')
                                    await reloadMes.add_reaction(sheduleEmoji)

                                answer = 'Успешно!'

                        command = self.config['privateCommands']['simpleVoiceCommand']
                        if msg.split()[0].lower() == command:
                            if message.author.id == self.config['usersIDs'].getint('yokoId'):
                                self.musicPlayer.simpleVoice(msg, command)
                                answer = 'Проговорила'

                        command = self.config['privateCommands']['simpleMessageCommand']
                        if msg.split()[0].lower() == command:
                            if message.author.id == self.config['usersIDs'].getint('yokoId'):
                                channel = await self.client.fetch_channel(788546742677143552)
                                await channel.send(msg.split(command)[1].strip())
                                answer = 'Написала'

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

                guildCommands = list(commands['guild']['usual'].keys()) + list(commands['guild']['music'].keys()) + list(commands['guild']['token'].keys()) + list(commands['guild']['moviegoers'].keys()) + list(commands['guild']['my'].keys())

                if isCommand(msg, guildCommands):
                    #await message.delete()
                    delay = 10
                    if str(message.channel.type) == 'text':
                        answer = 'Тебе низя использовать эту команду'
                        command = msg.split()[0].lower()
                        if isCommand(msg, commands['guild']['usual'].keys()):
                            com = False
                            for cmd in commands['guild']['usual'].keys():
                                if len(cmd.split()) > 1:
                                    if msg.lower().startswith(cmd):
                                        com = True
                                        command = cmd
                                else:
                                    if cmd == command:
                                        com = True

                            if com:
                                if commands['guild']['usual'][command]['function']:
                                    eval(commands['guild']['usual'][command]['function'])
                                    answer = commands['guild']['usual'][command]['answer']
                                else:
                                    answer = eval(commands['guild']['usual'][command]['answer'])
                                delay = commands['guild']['usual'][command]['delay']


                        if command in commands['guild']['music'].keys():
                            channel = await self.client.fetch_channel(self.config['data'].getint('kadrovyChannel'))
                            if message.author in channel.members:
                                if commands['guild']['music'][command]['function']:
                                    eval(commands['guild']['music'][command]['function'])
                                    answer = commands['guild']['music'][command]['answer']
                                else:
                                    answer = eval(commands['guild']['music'][command]['answer'])
                                delay = commands['guild']['music'][command]['delay']
                            else:
                                answer = 'Ты не находишься в войсе, бака!'
                                delay = None

                        '''
                        if command in commands['guild']['token'].keys():
                            if message.author.id in eval(self.config['token']['accessList']):
                                if commands['guild']['token'][command]['function']:
                                    eval(commands['guild']['token'][command]['function'])
                                    answer = commands['guild']['token'][command]['answer']
                                else:
                                    answer = eval(commands['guild']['token'][command]['answer'])
                                delay = commands['guild']['token'][command]['delay']
                        '''


                        if command in commands['guild']['moviegoers'].keys():
                            await message.delete()
                            if message.author.id in eval(self.config['sheduleData']['moviegoers']):
                                if commands['guild']['moviegoers'][command]['function']:
                                    eval(commands['guild']['moviegoers'][command]['function'])
                                    answer = commands['guild']['moviegoers'][command]['answer']
                                else:
                                    answer = eval(commands['guild']['moviegoers'][command]['answer'])
                                delay = commands['guild']['moviegoers'][command]['delay']


                        if command in commands['guild']['my'].keys():
                            await message.delete()
                            if message.author.id == self.config['usersIDs'].getint('yokoId'):
                                if commands['guild']['my'][command]['function']:
                                    eval(commands['guild']['my'][command]['function'])
                                    answer = commands['guild']['my'][command]['answer']
                                else:
                                    answer = eval(commands['guild']['my'][command]['answer'])
                                delay = commands['guild']['my'][command]['delay']

                        if len(answer) >= 2000:
                            for i in range(0, len(answer), 2000):
                                await message.channel.send(answer[i:i+2000], delete_after = delay)
                        else:
                            await message.channel.send(answer, delete_after = delay)


                    else:
                        await message.channel.send('<@{0}>, эта команда только для каналов'.format(UID), delete_after = 5)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print('New error:\ntype - {0}, line - {1}, error - {2}\n'.format(exc_type, exc_tb.tb_lineno, e))



        #except Exception as e:
            #exc_type, exc_obj, exc_tb = sys.exc_info()
            #newLog(exc_type, exc_obj, exc_tb, e)
