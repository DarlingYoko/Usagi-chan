import discord, time, os
from gtts import gTTS
from threading import Thread


def playAudio(self, file, timeout):
    time.sleep(timeout)
    try:
        self.musicPlayer.vc.play(discord.FFmpegPCMAudio(source = file), after=lambda e: print(f'music in channel has finished playing.'))
    except Exception as e:
        print(e)

    time.sleep(timeout)
    os.remove(file)


def setVoiceStateUpdateEvent(self):
    @self.client.event
    async def on_voice_state_update(member, before, after):

        try:
            if member.id == self.config['usersIDs'].getint('yokoId'):

                if before.channel and after.channel and before.channel.id != after.channel.id:
                    await discord.utils.get(self.client.voice_clients, channel=before.channel).disconnect()
                    self.musicPlayer.vc = await self.client.get_channel(after.channel.id).connect()

                elif before.channel and not after.channel:
                    await discord.utils.get(self.client.voice_clients, channel=before.channel).disconnect()
                    self.musicPlayer.vc = None

                elif after.channel and not before.channel:
                    self.musicPlayer.vc = await self.client.get_channel(after.channel.id).connect()
        except:
            pass


        try:
            #print(before.channel and not after.channel and before.channel.id == 788865135724068904 and member.id != self.config['usersIDs'].getint('yokoId') and member.id != self.config['usersIDs'].getint('botId'))
            #print(after.channel, not before.channel, after.channel.id == 733640826256752641, member.id != self.config['usersIDs'].getint('yokoId'), member.id != self.config['usersIDs'].getint('botId'))
            if before.channel and not after.channel and before.channel.id == 733640826256752641 and member.id != self.config['usersIDs'].getint('yokoId') and member.id != self.config['usersIDs'].getint('botId'):
                file = 'D:\Projects\Discord\Yoko-bot\\files\\audio\\{0}_vishel.mp3'.format(member.id)
                text = '{0} вышёл'.format(member.display_name)
                language = 'ru'
                speech = gTTS(text = text, lang = language, slow = False)
                speech.save(file)
                Thread(target=playAudio, args=(self, file, 5, )).start()


            elif after.channel and not before.channel and after.channel.id == 733640826256752641 and member.id != self.config['usersIDs'].getint('yokoId') and member.id != self.config['usersIDs'].getint('botId'):
                file = 'D:\Projects\Discord\Yoko-bot\\files\\audio\\{0}_voshel.mp3'.format(member.id)
                text = '{0} зашёл'.format(member.display_name)
                language = 'ru'
                speech = gTTS(text = text, lang = language, slow = False)
                speech.save(file)
                Thread(target=playAudio, args=(self, file, 5, )).start()
        except Exception as e:
            print(e)
